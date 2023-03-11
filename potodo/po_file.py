import itertools
import logging
import os
import pickle
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Dict, List, Optional, Sequence, Set, cast

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

    def counts(self) -> str:
        """Return a string representation with counts of untranslated and fuzzy."""
        missing = len(self.fuzzy_entries) + len(self.untranslated_entries)
        fuzzy_nb = self.fuzzy_nb if self.fuzzy_entries else 0
        fuzzy_str = f", including {fuzzy_nb} fuzzies." if fuzzy_nb else ""
        return f"- {self.filename:<30} {missing:3d} to do{fuzzy_str}."

    def percentages(self) -> str:
        """Return a string representation with pct of untranslated and fuzzy."""
        fuzzy_nb = self.fuzzy_nb if self.fuzzy_entries else 0
        fuzzy_str = f", {fuzzy_nb} fuzzy" if fuzzy_nb else ""
        return (
            f"- {self.filename:<30} {self.translated_nb:3d} / {self.po_file_size:3d}"
            f" ({self.percent_translated:5.1f}% translated){fuzzy_str}."
        )


class PoDirectoryStats:
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
        # self.cache is an in-memory cache, which can be optionally persisted on disk
        # using `.write_cache()` and `.read_cache()
        self.cache: Dict[Path, PoFileStats] = {}

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
        if path in self.cache:
            return self.cache[path]
        return PoFileStats(path)

    def stats_by_directory(self) -> Dict[Path, List[PoFileStats]]:
        return {
            directory: [self.stats_for_file(po_file) for po_file in po_files]
            for directory, po_files in self.files_by_directory().items()
        }

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
                self.cache[path] = stats

    def write_cache(self, cache_path: Path = Path(".potodo/cache.pickle")) -> None:
        """Persists all PoFileStats to disk."""
        os.makedirs(cache_path.parent, exist_ok=True)
        data = {"version": VERSION, "data": self.cache}
        with NamedTemporaryFile(
            mode="wb", delete=False, dir=str(cache_path.parent), prefix=cache_path.name
        ) as tmp:
            pickle.dump(data, tmp)
        os.rename(tmp.name, cache_path)
        logging.debug("Wrote PoDirectoryStats cache to %s", cache_path)
