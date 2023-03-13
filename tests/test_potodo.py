import json


def test_txt_output(run_potodo):
    captured = run_potodo(["--exclude", "excluded/", "excluded.po"])

    assert "file1.po" in captured.out
    assert "file2.po" in captured.out
    assert "# folder" in captured.out
    assert "file3.po" in captured.out
    assert "1 fuzzy" in captured.out
    assert "2 fuzzy" not in captured.out
    assert "excluded" not in captured.out


def test_output(run_potodo, repo_dir):
    output = json.loads(
        run_potodo(["--json", "--exclude", "excluded/", "excluded.po"]).out
    )

    expected_folder = {
        "name": "folder/",
        "percent_translated": 0.0,
        "files": [
            {
                "name": "folder/file3",
                "path": f"{repo_dir}/folder/file3.po",
                "entries": 1,
                "fuzzies": 0,
                "translated": 0,
                "percent_translated": 0,
                "reserved_by": None,
                "reservation_date": None,
            },
        ],
    }
    expected_repository = {
        "name": "repository/",
        "percent_translated": 25.0,
        "files": [
            {
                "name": "repository/file1",
                "path": f"{repo_dir}/file1.po",
                "entries": 3,
                "fuzzies": 1,
                "translated": 1,
                "percent_translated": 33,
                "reserved_by": None,
                "reservation_date": None,
            },
            {
                "name": "repository/file2",
                "path": f"{repo_dir}/file2.po",
                "entries": 1,
                "fuzzies": 0,
                "translated": 0,
                "percent_translated": 0,
                "reserved_by": None,
                "reservation_date": None,
            },
        ],
    }

    assert len(output) == 2
    for item in output:
        if item["name"] == "repository/":
            assert item == expected_repository
        if item["name"] == "folder/":
            assert item == expected_folder
