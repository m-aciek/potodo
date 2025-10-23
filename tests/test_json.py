import json

from potodo.potodo import main


def test_json_output(capsys, monkeypatch, repo_dir):
    monkeypatch.setattr(
        "sys.argv", ["potodo", "--json", "-p", str(repo_dir / "folder")]
    )
    main()
    out, _err = capsys.readouterr()
    assert "folder/excluded" in out
    assert "folder/file3" in out


def test_json_exclude_output(run_potodo, repo_dir):
    output = json.loads(
        run_potodo(["--json", "--exclude", "excluded/", "excluded.po"]).out
    )

    expected_folder = {
        "name": "folder/",
        "percent_translated": 53.84615384615385,
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
        "percent_translated": 21.73913043478261,
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
    for item in output["directories"]:
        if item["name"] == "repository/":
            assert item == expected_repository
        if item["name"] == "folder/":
            assert item == expected_folder
