import re
from pathlib import Path
from tempfile import TemporaryDirectory

from potodo.merge import sync_po_and_pot


def test_merges_file_in_main_directory(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        # polib adds an empty metadata https://github.com/izimobil/polib/issues/160
        assert (
            Path(tmp_dir, "file1.po").read_text(encoding="UTF-8")
            == """#
msgid ""
msgstr ""

#: /un/chemin/idiot.rst:666
msgid "We should translate this eventually"
msgstr ""

#: /un/chemin/idiot.rst:69
msgid "This is an updated dummy sentence."
msgstr ""

#~ msgid "This is a dummy sentence."
#~ msgstr "Ceci est une phrase bateau."

#, fuzzy
#~ msgid "Incredibly useful as a tool, this potodo"
#~ msgstr "Incroyablement inutile comme outil, ce potodo"

#~ msgid "Hello darkness my old friend"
#~ msgstr "Vous qui lisez cette ligne, vous tes trs beau."

#, fuzzy
#~ msgid "I am only there to make sure"
#~ msgstr "I don't get counted as a fuzzy entry"
"""
        )


def test_merges_a_file_in_a_subdirectory(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        assert (
            Path(tmp_dir, "folder/finished.po").read_text(encoding="UTF-8")
            == """#
msgid ""
msgstr ""

#: /un/chemin/idiot.rst:420
msgid "Incredibly useful as a tool, this potodo"
msgstr "Incroyablement inutile comme outil, ce potodo"
"""
        )


def test_skips_po_file_without_pot(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        assert not Path(tmp_dir, "file2.po").exists()


def test_skips_po_file_without_pot_in_a_subdirectory(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        assert not Path(tmp_dir, "folder/file3.po").exists()


def test_moves_pot_as_po_when_no_po(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        assert (
            Path(tmp_dir, "file3.po").read_text(encoding="UTF-8")
            == """msgid "This string is in source, but not yet in the translation"
msgstr ""
"""
        )


def test_moves_pot_as_po_when_no_po_in_a_subdirectory(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot([repo_dir], pots_dir, Path(tmp_dir))
        assert (
            Path(tmp_dir, "folder/file5.po").read_text(encoding="UTF-8")
            == """msgid "This string is in source in a subdirectory, but not yet in the translation"
msgstr ""
"""
        )


def test_run_without_dash_dash_pot(run_potodo):
    captured = run_potodo([])
    assert re.search("file1.po  .* 33.0% translated", captured.out)


def test_run_with_dash_dash_pot(run_potodo, repo_dir):
    pots_dir = repo_dir.parent / "pots"
    captured = run_potodo(["--pot", str(pots_dir)])
    assert re.search("file1.po  .* 0.0% translated", captured.out)
