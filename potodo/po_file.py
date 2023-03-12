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
    """

    def __init__(self, path: Path):
        """Initializes the class with all the correct information"""
        self.path: Path = path
        self.filename: str = path.name
        self.mtime = os.path.getmtime(path)
        self.pofile: polib.POFile = polib.pofile(str(self.path))
        self.directory: str = self.path.parent.name
        self.reserved_by: Optional[str] = None
        self.reservation_date: Optional[str] = None
        self.obsolete_entries: Sequence[polib.POEntry] = self.pofile.obsolete_entries()
        self.obsolete_nb: int = len(self.pofile.obsolete_entries())

        self.fuzzy_entries: List[polib.POEntry] = [
            entry for entry in self.pofile if entry.fuzzy and not entry.obsolete
        ]
        self.fuzzy_nb: int = len(self.fuzzy_entries)

        self.translated_entries: Sequence[
            polib.POEntry
        ] = self.pofile.translated_entries()
        self.translated_nb: int = len(self.translated_entries)

        self.untranslated_entries: Sequence[
            polib.POEntry
        ] = self.pofile.untranslated_entries()
        self.untranslated_nb: int = len(self.untranslated_entries)

        self.entries_count: int = len([e for e in self.pofile if not e.obsolete])
        self.percent_translated: int = self.pofile.percent_translated()
        self.po_file_size = len(self.pofile) - self.obsolete_nb
        self.filename_dir: str = self.directory + "/" + self.filename

    def __str__(self) -> str:
        return (
            f"Filename: {self.filename}\n"
            f"Fuzzy Entries: {self.fuzzy_entries}\n"
            f"Percent Translated: {self.percent_translated}\n"
            f"Translated Entries: {self.translated_entries}\n"
            f"Untranslated Entries: {self.untranslated_entries}"
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
        return len(self.fuzzy_entries) + len(self.untranslated_entries)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": f"{self.directory}/{self.filename.replace('.po', '')}",
            "path": str(self.path),
            "entries": self.po_file_size,
            "fuzzies": self.fuzzy_nb,
            "translated": self.translated_nb,
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
        return sum(po_file.translated_nb for po_file in self.files)

    @property
    def total(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(po_file.entries_count for po_file in self.files)

    @property
    def completion(self) -> float:
        """Return % of completion of this directory."""
        return 100 * self.translated / self.total

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
    """Represents a hierarchy of `.po` files."""

    def __init__(
        self, path: Path, filter_function: Optional[Callable[[str], bool]] = None
    ):
        """filter_function is a function to include/exclude po files
        or directories, it should return True for the file to be
        included.
        """
        self.path = path
        if filter_function is None:
            filter_function = self.allow_all
        self.filter_function = filter_function
        # self.files can be persisted on disk
        # using `.write_cache()` and `.read_cache()
        self.files: Dict[Path, PoFileStats] = {}

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(directory.translated for directory in self.stats_by_directory())

    @property
    def total(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(directory.total for directory in self.stats_by_directory())

    @property
    def completion(self) -> float:
        """Return % of completion of this project."""
        return 100 * self.translated / self.total

    @staticmethod
    def allow_all(path: str) -> bool:
        """Default filtering function: allow all files."""
        return True

    def find_all_files(self) -> List[Path]:
        """Get all the files matching `**/*.po`.
        File can be filtered using `self.filter_function`, see __init__.
        """
        return [
            file for file in self.path.rglob("*.po") if self.filter_function(str(file))
        ]

    def files_by_directory(self) -> Dict[Path, Set[Path]]:
        return {
            name: set(files)
            # We assume the output of rglob to be sorted,
            # so each 'name' is unique within groupby
            for name, files in itertools.groupby(
                self.find_all_files(), key=lambda path: path.parent
            )
        }

    def stats_for_file(self, path: Path) -> PoFileStats:
        """Get a PoFileStats for a given Path."""
        if path not in self.files:
            self.files[path] = PoFileStats(path)
        return self.files[path]

    def stats_by_directory(self) -> List[PoDirectoryStats]:
        return [
            PoDirectoryStats(
                directory, [self.stats_for_file(po_file) for po_file in po_files]
            )
            for directory, po_files in self.files_by_directory().items()
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
        for path, stats in cast(Dict[Path, PoFileStats], data["data"]).items():
            if os.path.getmtime(path.resolve()) == stats.mtime:
                self.files[path] = stats

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
