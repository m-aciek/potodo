import re


def test_potodo_no_args(run_potodo):
    output = run_potodo([]).out
    assert "excluded/  75.00% done" in output
    assert "folder/  58.82% done" in output
    assert re.search(r"excluded.po  * 1 /   2 \( 50.0% translated\)", output)
    assert re.search(r"file3.po   * 0 /   1 \(  0.0% translated\)", output)
    assert re.search(r"file1.po  * 1 /   3 \( 33.0% translated\), 1 fuzzy", output)
    assert "1 directory  40.91% done" in output


def test_potodo_exclude(run_potodo):
    output = run_potodo(["--exclude", "excluded/", "excluded.po"]).out
    output_short = run_potodo(["-e", "excluded/", "excluded.po"]).out
    assert output == output_short
    assert "excluded/  50.00% done" not in output
    assert "excluded.po" not in output
    assert "1 directory  33.33% done" in output
    assert re.search(r"file1.po  *  1 /   3 \( 33.0% translated\), 1 fuzzy", output)


def test_potodo_show_finished(run_potodo):
    output = run_potodo(["--show-finished"]).out
    output_short = run_potodo(["-s"]).out
    assert output == output_short
    assert "folder/  58.82% done" in output
    assert re.search(r"excluded.po    *  1 /   2 \( 50.0% translated\)", output)
    assert re.search(r"file3.po       *  0 /   1 \(  0.0% translated\)", output)
    assert re.search(r"finished.po    *  1 /   1 \(100.0% translated\)", output)


def test_potodo_above(run_potodo):
    output = run_potodo(["--above", "40"]).out
    output_short = run_potodo(["-a", "40"]).out
    assert output == output_short
    assert "file1.po" not in output
    assert "excluded.po                    1 /   2 ( 50.0% translated)" in output


def test_potodo_below(run_potodo):
    output = run_potodo(["--below", "40"]).out
    output_short = run_potodo(["-b", "40"]).out
    assert output == output_short
    assert re.search(r"file1.po  * 1 /   3 \( 33.0% translated\), 1 fuzzy", output)
    assert "excluded.po" not in output


def test_potodo_onlyfuzzy(run_potodo):
    output = run_potodo(["--only-fuzzy"]).out
    output_short = run_potodo(["-f"]).out
    assert output == output_short
    assert re.search(r"file1.po   * 1 /   3 \( 33.0% translated\), 1 fuzzy", output)
    assert "excluded.po" not in output


def test_potodo_counts(run_potodo):
    output = run_potodo(["--counts"]).out
    output_short = run_potodo(["-c"]).out
    assert output == output_short
    assert "% translated" not in output
    assert re.search("file4.po .*  1 to do", output)
    assert "repository/  40.91% done" in output
    assert re.search("file1.po *  2 to do, 1 fuzzy", output)


def test_potodo_exclude_fuzzy(run_potodo):
    output = run_potodo(["--exclude-fuzzy"]).out
    assert re.search(r"excluded.po  *  1 /   2 \( 50.0% translated\)", output)
    assert "file1.po" not in output


def test_potodo_matching_files_solo(run_potodo):
    output = run_potodo(["--matching-files"]).out
    output_short = run_potodo(["-l"]).out
    assert output == output_short
    assert "excluded/file4.po" in output
    assert "folder/excluded.po" in output
    assert "folder/file3.po" in output
    assert "file1.po" in output
    assert "file2.po" in output


def test_potodo_matching_files_fuzzy(run_potodo):
    output = run_potodo(["--matching-files", "--only-fuzzy"]).out
    output_short = run_potodo(["-l", "-f"]).out
    assert output == output_short
    assert "file1.po" in output


# Missing tests: Test hide_reserved, offline options, only_reserved,
# exclude_reserved, show_reservation_dates, Test verbose
# output levels
