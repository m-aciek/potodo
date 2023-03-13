import itertools
import logging
import os
import pickle
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional, Sequence, cast

import polib

from potodo import __version__ as VERSION


class PoFileStats:
    """Statistics about a po file.

    Contains all the necessary information about the progress of a given po file.
    """

    def __init__(self, path: Path):
        """Initializes the class with all the correct information"""
        self.path: Path = path
        self.filename: str = path.name
        self.mtime = os.path.getmtime(path)
        self.pofile: Optional[polib.POFile] = None
        self.directory: str = self.path.parent.name
        self.reserved_by: Optional[str] = None
        self.reservation_date: Optional[str] = None
        self.filename_dir: str = self.directory + "/" + self.filename

    @property
    def fuzzy(self) -> int:
        self.parse()
        assert self.pofile
        return len(
            [entry for entry in self.pofile if entry.fuzzy and not entry.obsolete]
        )

    @property
    def translated(self) -> int:
        self.parse()
        assert self.pofile
        return len(self.pofile.translated_entries())

    @property
    def untranslated(self) -> int:
        self.parse()
        assert self.pofile
        return len(self.pofile.untranslated_entries())

    @property
    def entries(self) -> int:
        self.parse()
        assert self.pofile
        return len([e for e in self.pofile if not e.obsolete])

    @property
    def percent_translated(self) -> int:
        self.parse()
        assert self.pofile
        return self.pofile.percent_translated()

    def parse(self) -> None:
        if self.pofile is None:
            self.pofile = polib.pofile(str(self.path))

    def __str__(self) -> str:
        return (
            f"Filename: {self.filename}\n"
            f"Fuzzy Entries: {self.fuzzy}\n"
            f"Percent Translated: {self.percent_translated}\n"
            f"Translated Entries: {self.translated}\n"
            f"Untranslated Entries: {self.untranslated}"
        )

    def __lt__(self, other: "PoFileStats") -> bool:
        """When two PoFiles are compared, their filenames are compared."""
        return self.filename < other.filename

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

    def __init__(self, path: Path, files: Sequence[PoFileStats]):
        self.path = path
        self.files = files

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(po_file.translated for po_file in self.files)

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(po_file.entries for po_file in self.files)

    @property
    def completion(self) -> float:
        """Return % of completion of this directory."""
        return 100 * self.translated / self.entries

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.path == other.path

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.path < other.path

    def __le__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.path <= other.path

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.path > other.path

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.path >= other.path


class PoProjectStats:
    """Represents the root of the hierarchy of `.po` files."""

    def __init__(self, path: Path):
        self.path = path
        # self.files can be persisted on disk
        # using `.write_cache()` and `.read_cache()
        self.files: List[PoFileStats] = []

    def filter(self, filter_func: Callable[[PoFileStats], bool]) -> None:
        self.files = [po_file for po_file in self.files if filter_func(po_file)]

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(directory.translated for directory in self.stats_by_directory())

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(directory.entries for directory in self.stats_by_directory())

    @property
    def completion(self) -> float:
        """Return % of completion of this project."""
        return 100 * self.translated / self.entries

    def rescan(self) -> None:
        """Scan disk to search for po files.

        This is the only function that hit the disk.
        """
        for path in list(self.path.rglob("*.po")):
            if path not in self.files:
                self.files.append(PoFileStats(path))

    def stats_by_directory(self) -> List[PoDirectoryStats]:
        return [
            PoDirectoryStats(directory, list(po_files))
            for directory, po_files in itertools.groupby(
                self.files, key=lambda po_file: po_file.path.parent
            )
        ]

    def read_cache(
        self,
        cache_path: Path = Path(".potodo/cache.pickle"),
    ) -> None:
        """Restore all PoFileStats from disk.

        While reading the cache, outdated entires are **not** loaded.
        """
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
                self.files.append(po_file)

    def write_cache(self, cache_path: Path = Path(".potodo/cache.pickle")) -> None:
        """Persists all PoFileStats to disk."""
        os.makedirs(cache_path.parent, exist_ok=True)
        data = {"version": VERSION, "data": self.files}
        with NamedTemporaryFile(
            mode="wb", delete=False, dir=str(cache_path.parent), prefix=cache_path.name
        ) as tmp:
            pickle.dump(data, tmp)
        os.rename(tmp.name, cache_path)
        logging.debug("Wrote PoProjectStats cache to %s", cache_path)
