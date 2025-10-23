from potodo.potodo import main


def test_git(capsys, monkeypatch, fixtures_dir):
    """Ensure than excluded files are **not** parsed.

    Parsing excluded files can lead to surprises, here, parsing a
    `.po` file in `.git` may not work, it may just be a branch or
    whatever and contain a sha1 instead.

    I name it dotgit instead of .git, to not scare git.
    """
    monkeypatch.setattr(
        "sys.argv", ["potodo", "-p", str(fixtures_dir / "has_potodoignore")]
    )
    main()
    out, _err = capsys.readouterr()
    assert "venv" not in out
    assert "not" in out
