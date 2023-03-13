def test_potodo_help(run_potodo):
    output = run_potodo(["--help"]).out
    output_short = run_potodo(["-h"]).out
    assert output == output_short
    assert "-h, --help            show this help message and exit" in output


def test_potodo_above_below_conflict(run_potodo):
    output = run_potodo(["--above", "50", "--below", "40"]).err
    output_short = run_potodo(["-a", "50", "-b", "40"]).err
    assert (
        output
        == output_short
        == "Potodo: 'below' value must be greater than 'above' value.\n"
    )


def test_potodo_json_interactive_conflict(run_potodo):
    output = run_potodo(["--json", "--interactive"]).err
    output_short = run_potodo(["-j", "-i"]).err
    assert (
        output
        == output_short
        == "Potodo: Json format and interactive modes cannot be activated at the same time.\n"
    )


def test_potodo_exclude_and_only_fuzzy_conflict(run_potodo):
    output = run_potodo(["--exclude-fuzzy", "--only-fuzzy"]).err
    assert (
        output
        == "Potodo: Cannot pass --exclude-fuzzy and --only-fuzzy at the same time.\n"
    )


def test_potodo_exclude_and_only_reserved_conflict(run_potodo):
    output = run_potodo(["--exclude-reserved", "--only-reserved"]).err
    assert (
        output
        == "Potodo: Cannot pass --exclude-reserved and --only-reserved at the same time.\n"
    )
