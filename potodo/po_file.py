import itertools
import logging
import os
from pathlib import Path
from typing import Callable, Optional
from typing import Dict
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Set

import polib


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


from potodo.cache import get_cache_file_content  # noqa
from potodo.cache import set_cache_content  # noqa


class PODirectory:
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

    def stats_by_directory(self) -> Dict[Path, List[PoFileStats]]:
        return {
            directory: [PoFileStats(po_file) for po_file in po_files]
            for directory, po_files in self.files_by_directory().items()
        }


def get_po_stats_from_repo_or_cache(
    repo_path: Path,
    ignore_matches: Callable[[str], bool],
    no_cache: bool = False,
) -> Mapping[Path, List[PoFileStats]]:
    """Gets all the po files recursively from 'repo_path'
    and cache if no_cache is set to False, excluding those if ignore_matches match them.
    Return a dict with all directories and PoFile instances of
    `.po` files in those directories.
    """

    logging.debug("Finding po files in %s", repo_path)
    po_directory = PODirectory(repo_path, lambda file: not ignore_matches(file))

    if no_cache:
        logging.debug("Creating PoFileStats objects for each file without cache")
        return po_directory.stats_by_directory()
    else:
        cached_files = get_cache_file_content(
            path=str(repo_path.resolve()) + "/.potodo/cache.pickle",
        )
        po_files_per_directory = po_directory.files_by_directory()
        po_stats_per_directory: Dict[Path, List[PoFileStats]] = {}
        for directory, po_files in po_files_per_directory.items():
            po_stats_per_directory[directory] = []
            for po_file in po_files:
                cached_file = cached_files.get(po_file.resolve())
                if not (
                    cached_file
                    and os.path.getmtime(po_file.resolve()) == cached_file.mtime
                ):
                    cached_files[po_file.resolve()] = cached_file = PoFileStats(po_file)
                po_stats_per_directory[directory].append(cached_file)
        set_cache_content(
            cached_files,
            path=str(repo_path.resolve()) + "/.potodo/cache.pickle",
        )

    return po_stats_per_directory
