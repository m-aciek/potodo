"""Test that filtering works correctly with relative paths.

This test ensures that the ValueError:
  'X is not in the subpath of Y'
does not occur when using relative paths with the Python API.

See: https://github.com/m-aciek/potodo/issues/XXX
"""
import os
from pathlib import Path

import pytest

from potodo.arguments_handling import Filters
from potodo.po_file import PoDirectories


def test_filter_with_relative_path(tmp_path):
    """Test that filter() works when PoDirectory is created with a relative path.
    
    This reproduces the issue where gitignore_parser would fail with:
        ValueError: '/absolute/path/file.po' is not in the subpath of 'relative/path'
    
    The fix ensures that both the rule base paths and file paths are resolved
    to absolute paths before matching.
    """
    # Create test directory structure
    test_dir = tmp_path / "test_repo"
    test_dir.mkdir()
    
    bugs_po = test_dir / "bugs.po"
    tutorial_po = test_dir / "tutorial" / "intro.po"
    lib_po = test_dir / "library" / "functions.po"
    
    tutorial_po.parent.mkdir(parents=True)
    lib_po.parent.mkdir(parents=True)
    
    # Create minimal PO file content
    po_content = '''msgid ""
msgstr ""

msgid "test"
msgstr ""
'''
    bugs_po.write_text(po_content)
    tutorial_po.write_text(po_content)
    lib_po.write_text(po_content)
    
    # Save current directory
    orig_dir = os.getcwd()
    
    try:
        # Change to parent of test_dir to use relative path
        os.chdir(tmp_path)
        
        # Use relative path (this triggers the issue)
        relative_path = Path("test_repo")
        
        # Create PoDirectories with relative path
        project = PoDirectories.from_paths([relative_path])
        
        assert len(project[0].files) == 3
        
        # This should NOT raise ValueError
        # The exact pattern from the original issue report
        project.filter(
            filters=Filters(False, True, 0, 100, False, False),
            exclude=['**/*', '!bugs.po', '!tutorial/', '!library/functions.po'],
        )
        
        # The filter should complete without error
        # (The specific files included/excluded depend on gitignore_parser behavior)
        assert len(project[0].files) >= 1
        
    finally:
        os.chdir(orig_dir)


def test_filter_with_absolute_path(tmp_path):
    """Test that filter() still works correctly with absolute paths."""
    # Create test directory structure
    test_dir = tmp_path / "test_repo"
    test_dir.mkdir()
    
    bugs_po = test_dir / "bugs.po"
    other_po = test_dir / "other.po"
    
    po_content = '''msgid ""
msgstr ""

msgid "test"
msgstr ""
'''
    bugs_po.write_text(po_content)
    other_po.write_text(po_content)
    
    # Use absolute path
    absolute_path = test_dir.resolve()
    
    # Create PoDirectories with absolute path
    project = PoDirectories.from_paths([absolute_path])
    
    assert len(project[0].files) == 2
    
    # Filter should work correctly
    project.filter(
        filters=Filters(False, True, 0, 100, False, False),
        exclude=['**/*', '!bugs.po'],
    )
    
    # Only bugs.po should remain
    assert len(project[0].files) == 1
    assert list(project[0].files)[0].filename == 'bugs.po'
