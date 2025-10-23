from potodo.potodo import main


def test_git(capsys, monkeypatch, git_repo_dir):
    """Ensure than excluded files are **not** parsed.

    Parsing excluded files can lead to surprises, here, parsing a
    `.po` file in `.git` may not work, it may just be a branch or
    whatever and contain a sha1 instead.

    I name it dotgit instead of .git, to not scare git.
    """
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(git_repo_dir), "--exclude", "dotgit/"]
    )
    main()
    out, _err = capsys.readouterr()
    assert "file1" in out


def test_no_exclude(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr("sys.argv", ["potodo", "-p", str(repo_dir)])
    main()
    out, _err = capsys.readouterr()
    assert "file1" in out
    assert "file2" in out
    assert "file3" in out


def test_exclude_file(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(repo_dir), "--exclude", "file*"]
    )
    main()
    out, _err = capsys.readouterr()
    assert "file1" not in out
    assert "file2" not in out
    assert "file3" not in out
    assert "excluded" in out  # The only one not being named file


def test_exclude_directory(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(repo_dir), "--exclude", "excluded/*"]
    )
    main()
    out, _err = capsys.readouterr()
    assert "file1" in out
    assert "file2" in out
    assert "file3" in out
    assert "file4" not in out  # in the excluded/ directory
    assert "excluded/" not in out


def test_exclude_single_file(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(repo_dir), "--exclude", "file2.po"]
    )
    main()
    out, _err = capsys.readouterr()
    assert "file1" in out
    assert "file2" not in out
    assert "file3" in out
    assert "file4" in out


def test_negation(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(repo_dir), "--exclude", "file*", "!file2.po"]
    )
    main()
    out, _err = capsys.readouterr()
    assert "file1" not in out
    assert "file2.po" in out
    assert "file3" not in out
    assert "excluded" in out
