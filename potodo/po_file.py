from __future__ import annotations

import logging
import os
import pickle
from functools import cached_property
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional, Set, cast

import polib
from gitignore_parser import handle_negation, rule_from_pattern

from potodo import __version__ as VERSION
from potodo.arguments_handling import Filters
from potodo.forge_api import get_issue_reservations


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
    def translated_words(self) -> int:
        self.parse()
        return self.stats["translated_words"]

    @property
    def untranslated(self) -> int:
        self.parse()
        return self.stats["untranslated"]

    @property
    def entries(self) -> int:
        self.parse()
        return self.stats["entries"]

    @property
    def words(self) -> int:
        self.parse()
        return self.stats["words"]

    @property
    def percent_translated(self) -> int:
        self.parse()
        return self.stats["percent_translated"]

    def parse(self) -> None:
        if self.stats:
            return  # Stats already computed.
        pofile = polib.pofile(self.path)
        self.stats = {
            "fuzzy": len(
                [entry for entry in pofile if entry.fuzzy and not entry.obsolete]
            ),
            "percent_translated": pofile.percent_translated(),
            "entries": len([e for e in pofile if not e.obsolete]),
            # use pofile.total_words() when
            # https://github.com/izimobil/polib/pull/166 is merged
            "words": sum(len(e.msgid.split()) for e in pofile if not e.obsolete),
            "untranslated": len(pofile.untranslated_entries()),
            "translated": len(pofile.translated_entries()),
            # use pofile.translated_words() when
            # https://github.com/izimobil/polib/pull/166 is merged
            "translated_words": sum(
                len(e.msgid.split()) for e in pofile.translated_entries()
            ),
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


class PoDirectories(list):
    """Collection of PoDirectory.

    Each PoDirectory can represent a hiearchy that have no common
    parent with the others.
    """

    @classmethod
    def from_paths(cls, paths: list[Path]) -> PoDirectories:
        self = cls()
        for path in paths:
            directory = PoDirectory(path)
            directory.scan()
            self.append(directory)
        return self

    def as_dict(self):
        """Used by json serialisation."""
        return {
            "percent_translated": self.completion,
            "directories": [
                po_directory.as_dict() for po_directory in self.subdirectories
            ],
        }

    def fetch_issues(self, api_url) -> None:
        for directory in self:
            directory.fetch_issues(api_url)

    @property
    def subdirectories(self) -> list[PoDirectory]:
        """Behave like PoDirectory's .subdirectories."""
        return self

    @property
    def immediate_files(self) -> set[PoFileStats]:
        """Behave like PoDirectory's .subdirectories."""
        return set()

    @property
    def translated_words(self) -> int:
        """Qty of translated words in the po files of this directory."""
        return sum(po_dir.translated_words for po_dir in self)

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(po_dir.entries for po_dir in self)

    @property
    def words(self) -> int:
        """Qty of words in the po files of this directory."""
        return sum(po_dir.words for po_dir in self)

    @property
    def completion(self) -> float:
        """Return % of completion of this directory."""
        try:
            return 100 * self.translated_words / self.words
        except ZeroDivisionError:
            return 0

    def filter(self, filters: Filters, exclude: list[str]) -> None:
        for directory in self:
            directory.filter(filters, exclude)


class PoDirectory:
    """Represents the root of the hierarchy of `.po` files."""

    def __init__(self, path: Path, use_cache=True):
        self.path = path
        self.files: Set[PoFileStats] = set()
        self.excluded_files: Set[PoFileStats] = set()
        self.use_cache = use_cache
        self.ignore_matcher: Callable[[str], bool] | None = None

    def __repr__(self):
        return f"<PoDirectory with {len(self.files)} files>"

    def as_dict(self):
        """Used by json serialisation."""
        return {
            "name": self.path.name,
            "percent_translated": self.completion,
            "files": [po_file.as_dict() for po_file in sorted(self.files)],
            "directories": [
                po_directory.as_dict() for po_directory in self.subdirectories
            ],
        }

    def _parse_potodoignore(self, exclude: List[str]) -> Callable[[str], bool]:
        rules = []
        potodo_ignore = self.path / ".potodoignore"
        if potodo_ignore.exists():
            for line in potodo_ignore.read_text().splitlines():
                rule = rule_from_pattern(line, self.path)
                if rule:
                    rules.append(rule)
        rules.append(rule_from_pattern(".git/", self.path))
        for rule in exclude:
            rules.append(rule_from_pattern(rule, self.path))
        if any(r.negation for r in rules):
            # We have negation rules. We can't use a simple "any" to evaluate them.
            # Later rules override earlier rules.
            return lambda file_path: handle_negation(file_path, rules)
        return lambda file_path: any(r.match(file_path) for r in rules)

    def _select(self, po_file: PoFileStats, filters: Filters) -> bool:
        """Return True if the po_file should be displayed, False otherwise."""
        assert self.ignore_matcher

        if self.ignore_matcher(str(po_file.path)):
            return False
        if filters.only_fuzzy and not po_file.fuzzy:
            return False
        if filters.exclude_fuzzy and po_file.fuzzy:
            return False
        if (
            po_file.percent_translated < filters.above
            or po_file.percent_translated > filters.below
        ):
            return False

        # unless the offline/hide_reservation are enabled
        if filters.exclude_reserved and po_file.reserved_by:
            return False
        if filters.only_reserved and not po_file.reserved_by:
            return False

        return True

    def filter(self, filters: Filters, exclude: List[str]) -> None:
        """Filter files according to a filter function.

        If filter is applied multiple times, it behave like only last
        filter has been applied.
        """

        if self.ignore_matcher is None:
            self.ignore_matcher = self._parse_potodoignore(exclude)

        all_files = self.files | self.excluded_files
        self.files = set()
        self.excluded_files = set()
        for file in all_files:
            if self._select(file, filters):
                self.files.add(file)
            else:
                self.excluded_files.add(file)

    def scan(self) -> None:
        """Scan disk to search for po files.

        This is the only function that hit the disk.
        """
        if self.use_cache:
            self._read_cache()
        for file in self.path.rglob("*.po"):
            if PoFileStats(file) not in self.files:
                self.files.add(PoFileStats(file))
        if self.use_cache:
            self._write_cache()

    @cached_property
    def subdirectories(self) -> list[PoDirectory]:
        subdirectories = [
            PoDirectory(dir, use_cache=self.use_cache)
            for dir in self.path.iterdir()
            if dir.is_dir() and not dir.name.startswith(".")
        ]
        for subdirectory in subdirectories:
            subdirectory.files = set(
                file
                for file in self.files
                if file.path.is_relative_to(subdirectory.path)
            )
        return [subdirectory for subdirectory in subdirectories if subdirectory.files]

    @property
    def immediate_files(self) -> set[PoFileStats]:
        """Files in this directory (not its descendents)."""
        files = [file for file in self.path.iterdir() if file.is_file()]
        return set(po_file for po_file in self.files if po_file.path in files)

    def _read_cache(self) -> None:
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
        except Exception:  # pylint: disable=broad-exception-caught
            logging.warning("Corrupted cache (maybe from another Python version)")
            return
        logging.debug("Found cache")
        if data.get("version") != VERSION:
            logging.info("Found old cache, ignored it.")
            return
        for po_file in cast(List[PoFileStats], data["data"]):
            try:
                if os.path.getmtime(po_file.path.resolve()) == po_file.mtime:
                    self.files.add(po_file)
            except FileNotFoundError:
                pass  # The file is in the cache but no longer on the filesystem.

    def _write_cache(self) -> None:
        """Persists all PoFileStats to disk."""
        cache_path = self.path / ".potodo" / "cache.pickle"
        os.makedirs(cache_path.parent, exist_ok=True)
        data = {"version": VERSION, "data": self.files | self.excluded_files}
        with NamedTemporaryFile(
            mode="wb", delete=False, dir=str(cache_path.parent), prefix=cache_path.name
        ) as tmp:
            pickle.dump(data, tmp)
        os.rename(tmp.name, cache_path)
        logging.debug("Wrote PoDirectory cache to %s", cache_path)

    def fetch_issues(self, api_url):
        issue_reservations = get_issue_reservations(api_url)
        for po_file_stats in self.files:
            reserved_by, reservation_date = issue_reservations.get(
                po_file_stats.filename_dir.lower(), (None, None)
            )
            if reserved_by and reservation_date:
                po_file_stats.reserved_by = reserved_by
                po_file_stats.reservation_date = reservation_date
            else:  # Just in case we remember it's reserved from the cache:
                po_file_stats.reserved_by = None
                po_file_stats.reservation_date = None

    @property
    def translated(self) -> int:
        """Qty of translated entries in the po files of this directory."""
        return sum(po_file.translated for po_file in self.files)

    @property
    def translated_words(self) -> int:
        """Qty of translated words in the po files of this directory."""
        return sum(po_file.translated_words for po_file in self.files)

    @property
    def entries(self) -> int:
        """Qty of entries in the po files of this directory."""
        return sum(po_file.entries for po_file in self.files)

    @property
    def words(self) -> int:
        """Qty of words in the po files of this directory."""
        return sum(po_file.words for po_file in self.files)

    @property
    def completion(self) -> float:
        """Return % of completion of this directory."""
        try:
            return 100 * self.translated_words / self.words
        except ZeroDivisionError:
            return 0

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
