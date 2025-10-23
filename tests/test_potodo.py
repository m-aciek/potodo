def test_txt_output(run_potodo):
    captured = run_potodo(["--exclude", "excluded/", "excluded.po"])

    assert "file1.po" in captured.out
    assert "file2.po" in captured.out
    assert "folder/" in captured.out
    assert "file3.po" in captured.out
    assert "1 fuzzy" in captured.out
    assert "2 fuzzy" not in captured.out
    assert "excluded" not in captured.out
