from pathlib import Path

from potodo.potodo import main

REPO_DIR = Path(__file__).resolve().parent / "fixtures" / "repository"


def test_no_exclude(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["potodo", "-p", str(REPO_DIR)])
    main()
    out, err = capsys.readouterr()
    assert not err
    assert "file1" in out
    assert "file2" in out
    assert "file3" in out


def test_exclude_file(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(REPO_DIR), "--exclude", "file*"]
    )
    main()
    out, err = capsys.readouterr()
    assert not err
    assert "file1" not in out
    assert "file2" not in out
    assert "file3" not in out
    assert "excluded" in out  # The only one not being named file


def test_exclude_directory(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(REPO_DIR), "--exclude", "excluded/*"]
    )
    main()
    out, err = capsys.readouterr()
    assert not err
    assert "file1" in out
    assert "file2" in out
    assert "file3" in out
    assert "file4" not in out  # in the excluded/ directory
    assert "excluded/" not in out


def test_exclude_single_file(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(REPO_DIR), "--exclude", "file2.po"]
    )
    main()
    out, err = capsys.readouterr()
    assert not err
    assert "file1" in out
    assert "file2" not in out
    assert "file3" in out
    assert "file4" in out
