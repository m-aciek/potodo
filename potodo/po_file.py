import itertools
import logging
import os
import pickle
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, cast

import polib

from potodo import __version__ as VERSION


class PoFileStats:
    """Statistics about a po file.

    Contains all the necessary information about the progress of a given po file.

    Beware this file is pickled (for the cache), don't store actual
    entries in its __dict__, just stats.
    """

    def __init__(self, path: Path):
        """Initializes the class with all the correct information"""
        self.path: Path = path
        self.filename: str = path.name
        self.mtime = os.path.getmtime(path)
        self.directory: str = self.path.parent.name
        self.reserved_by: Optional[str] = None
        self.reservation_date: Optional[str] = None
        self.filename_dir: str = self.directory + "/" + self.filename
        self.stats: Dict[str, int] = {}

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.path == other.path

    def __hash__(self) -> int:
        return hash(("PoFileStats", self.path))

    @property
    def fuzzy(self) -> int:
        self.parse()
        return self.stats["fuzzy"]

    @property
    def translated(self) -> int:
        self.parse()
        return self.stats["translated"]

    @property
    def untranslated(self) -> int:
        self.parse()
        return self.stats["untranslated"]

    @property
    def entries(self) -> int:
        self.parse()
        return self.stats["entries"]

    @property
    def percent_translated(self) -> int:
        self.parse()
        return self.stats["percent_translated"]

    def parse(self) -> None:
        if self.stats:
            return  # Stats already computed.
        pofile = polib.pofile(str(self.path))
        self.stats = {
            "fuzzy": len(
                [entry for entry in pofile if entry.fuzzy and not entry.obsolete]
            ),
            "percent_translated": pofile.percent_translated(),
            "entries": len([e for e in pofile if not e.obsolete]),
            "untranslated": len(pofile.untranslated_entries()),
            "translated": len(pofile.translated_entries()),
        }

    def __repr__(self) -> str:
        if self.stats:
            return f"<PoFileStats {self.path!r} {self.entries} entries>"
        return f"<PoFileStats {self.path!r} (unparsed)>"

    def __lt__(self, other: "PoFileStats") -> bool:
        """When two PoFiles are compared, their filenames are compared."""
        return self.path < other.path

    def reservation_str(self, with_reservation_dates: bool = False) -> str:
        if self.reserved_by is None:
            return ""
        as_string = f"reserved by {self.reserved_by}"
        if with_reservation_dates:
            as_string += f" ({self.reservation_date})"
        return as_string

    @property
    def missing(self) -> int:
        return self.fuzzy + self.untranslated

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": f"{self.directory}/{self.filename.replace('.po', '')}",
            "path": str(self.path),
            "entries": self.entries,
            "fuzzies": self.fuzzy,
            "translated": self.translated,
            "percent_translated": self.percent_translated,
            "reserved_by": self.reserved_by,
            "reservation_date": self.reservation_date,
        }


class PoDirectoryStats:
    """Represent a directory containing multiple `.po` files."""

    def __init__(self, path: Path, files_stats: Sequence[PoFileStats]):
        self.path = path
        self.files_stats = files_stats

    def __repr__(self) -> str:
        return f"<PoDirectoryStats {self.path!r} with {len(self.files_stats)} files>"

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(po_file.translated for po_file in self.files_stats)

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(po_file.entries for po_file in self.files_stats)

    @property
    def completion(self) -> float:
        """Return % of completion of this directory."""
        return 100 * self.translated / self.entries

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.path == other.path

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.path < other.path

    def __le__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.path <= other.path

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.path > other.path

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.path >= other.path


class PoProjectStats:
    """Represents the root of the hierarchy of `.po` files."""

    def __init__(self, path: Path):
        self.path = path
        # self.files can be persisted on disk
        # using `.write_cache()` and `.read_cache()
        self.files: Set[PoFileStats] = set()
        self.excluded_files: Set[PoFileStats] = set()

    def filter(self, filter_func: Callable[[PoFileStats], bool]) -> None:
        """Filter files according to a filter function.

        If filter is applied multiple times, it behave like only last
        filter has been applied.
        """
        all_files = self.files | self.excluded_files
        self.files = set()
        self.excluded_files = set()
        for file in all_files:
            if filter_func(file):
                self.files.add(file)
            else:
                self.excluded_files.add(file)

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(
            directory_stats.translated for directory_stats in self.stats_by_directory()
        )

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(
            directory_stats.entries for directory_stats in self.stats_by_directory()
        )

    @property
    def completion(self) -> float:
        """Return % of completion of this project."""
        return 100 * self.translated / self.entries

    def rescan(self) -> None:
        """Scan disk to search for po files.

        This is the only function that hit the disk.
        """
        for path in list(self.path.rglob("*.po")):
            if PoFileStats(path) not in self.files:
                self.files.add(PoFileStats(path))

    def stats_by_directory(self) -> List[PoDirectoryStats]:
        return [
            PoDirectoryStats(directory, list(po_files))
            for directory, po_files in itertools.groupby(
                sorted(self.files, key=lambda po_file: po_file.path.parent),
                key=lambda po_file: po_file.path.parent,
            )
        ]

    def read_cache(self) -> None:
        """Restore all PoFileStats from disk.

        While reading the cache, outdated entires are **not** loaded.
        """
        cache_path = self.path / ".potodo" / "cache.pickle"

        logging.debug("Trying to load cache from %s", cache_path)
        try:
            with open(cache_path, "rb") as handle:
                data = pickle.load(handle)
        except FileNotFoundError:
            logging.warning("No cache found")
            return
        logging.debug("Found cache")
        if data.get("version") != VERSION:
            logging.info("Found old cache, ignored it.")
            return
        for po_file in cast(List[PoFileStats], data["data"]):
            if os.path.getmtime(po_file.path.resolve()) == po_file.mtime:
                self.files.add(po_file)

    def write_cache(self) -> None:
        """Persists all PoFileStats to disk."""
        cache_path = self.path / ".potodo" / "cache.pickle"
        os.makedirs(cache_path.parent, exist_ok=True)
        data = {"version": VERSION, "data": self.files | self.excluded_files}
        with NamedTemporaryFile(
            mode="wb", delete=False, dir=str(cache_path.parent), prefix=cache_path.name
        ) as tmp:
            pickle.dump(data, tmp)
        os.rename(tmp.name, cache_path)
        logging.debug("Wrote PoProjectStats cache to %s", cache_path)
