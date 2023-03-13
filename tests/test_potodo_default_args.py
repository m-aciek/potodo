def test_potodo_no_args(run_potodo):
    output = run_potodo([]).out
    assert "# excluded (50.00% done)" in output
    assert "# folder (33.33% done)" in output
    assert "- excluded.po                      1 /   2 ( 50.0% translated)" in output
    assert "- file3.po                         0 /   1 (  0.0% translated)" in output
    assert "# repository (25.00% done)" in output
    assert (
        "- file1.po                         1 /   3 ( 33.0% translated), 1 fuzzy"
        in output
    )


def test_potodo_exclude(run_potodo):
    output = run_potodo(["--exclude", "excluded/", "excluded.po"]).out
    output_short = run_potodo(["-e", "excluded/", "excluded.po"]).out
    assert output == output_short
    assert "# excluded (50.00% done)" not in output
    assert (
        "- excluded.po                      1 /   2 ( 50.0% translated)" not in output
    )
    assert "# repository (25.00% done)" in output
    assert (
        "- file1.po                         1 /   3 ( 33.0% translated), 1 fuzzy"
        in output
    )


def test_potodo_above(run_potodo):
    output = run_potodo(["--above", "40"]).out
    output_short = run_potodo(["-a", "40"]).out
    assert output == output_short
    assert (
        "- file1.po                         1 /   3 ( 33.0% translated), 1 fuzzy"
        not in output
    )
    assert "- excluded.po                      1 /   2 ( 50.0% translated)" in output


def test_potodo_below(run_potodo):
    output = run_potodo(["--below", "40"]).out
    output_short = run_potodo(["-b", "40"]).out
    assert output == output_short
    assert (
        "- file1.po                         1 /   3 ( 33.0% translated), 1 fuzzy"
        in output
    )
    assert (
        "- excluded.po                      1 /   2 ( 50.0% translated)" not in output
    )


def test_potodo_onlyfuzzy(run_potodo):
    output = run_potodo(["--only-fuzzy"]).out
    output_short = run_potodo(["-f"]).out
    assert output == output_short
    assert (
        "- file1.po                         1 /   3 ( 33.0% translated), 1 fuzzy"
        in output
    )
    assert (
        "- excluded.po                      1 /   2 ( 50.0% translated)" not in output
    )


def test_potodo_counts(run_potodo):
    output = run_potodo(["--counts"]).out
    output_short = run_potodo(["-c"]).out
    assert output == output_short
    assert (
        "- excluded.po                      1 /   2 ( 50.0% translated)" not in output
    )
    assert "- file4.po                         1 to do" in output
    assert "# repository (25.00% done)" in output
    assert "- file1.po                         2 to do, 1 fuzzy." in output


def test_potodo_exclude_fuzzy(run_potodo):
    output = run_potodo(["--exclude-fuzzy"]).out
    assert "- excluded.po                      1 /   2 ( 50.0% translated)" in output
    assert "- file1.po                         2 to do, 1 fuzzy." not in output


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


# TODO: Test hide_reserved, offline options, only_reserved, exclude_reserved, show_reservation_dates
# TODO: Test verbose output levels
