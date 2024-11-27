from pathlib import Path
from tempfile import TemporaryDirectory

from potodo.merge import sync_po_and_pot

# test_merge:
# 1. regular case of merging
# 2. regular case of merging in a directory
# 3. no pot, po not considered
# 4. no pot, po in directory not considered
# 5. pot, no po: considered empty
# 6. pot in directory, no po: considered empty


def test_merges_file_in_main_directory(repo_dir):
    pots_dir = repo_dir.parent / "pots"
    with TemporaryDirectory() as tmp_dir:
        sync_po_and_pot(repo_dir, pots_dir, Path(tmp_dir))
        assert (
            Path(tmp_dir, "file1.po").read_text()
            == """#: /un/chemin/idiot.rst:69
msgid "This is an updated dummy sentence."
msgstr ""

#: /un/chemin/idiot.rst:666
msgid "We should translate this eventually"
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
