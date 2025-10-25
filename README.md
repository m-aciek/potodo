<p align="center">
    <img width=60% src="https://git.afpy.org/AFPy/potodo/raw/branch/main/media/Potodo.png">
</p>
<p align="center">
    <a href="https://woodpecker.afpy.org/AFPy/potodo"><img src="https://woodpecker.afpy.org/api/badges/AFPy/potodo/status.svg"></a>
    <img src="https://img.shields.io/pypi/v/potodo?color=green">
    <img src="https://img.shields.io/badge/python-v3.10+-green.svg">
    <img src="https://img.shields.io/badge/license-MIT-green.svg">
</p>

## What is it ?

Potodo is a TODO/progress listing CLI tool for po files.


### Potodo is part of poutils!

[Poutils](https://pypi.org/project/poutils) (`.po` utils) is is a metapackage to easily install usefull Python tools to use with po files
and `potodo` is a part of it! Go check out [Poutils](https://pypi.org/project/poutils) to discover the other useful tools for `po` file related translation!


## Installation

```sh
pip install potodo
```

## Usage example

When ran in the [french CPython documentation
translation](https://git.afpy.org/AFPy/python-docs-fr/) it shows:

```
$ potodo tutorial/ faq/
2 directories  84.80% done
├── tutorial/  84.98% done
│   ├── appendix.po                       17 /  24 ( 70.0% translated), 3 fuzzy
│   ├── classes.po                       114 / 116 ( 98.0% translated), 2 fuzzy
│   ├── controlflow.po                   146 / 152 ( 96.0% translated), 5 fuzzy
│   ├── datastructures.po                 78 /  91 ( 85.0% translated), 12 fuzzy
│   ├── errors.po                         66 /  70 ( 94.0% translated), 3 fuzzy
│   ├── floatingpoint.po                  20 /  48 ( 41.0% translated), 26 fuzzy
│   ├── index.po                           7 /   9 ( 77.0% translated), 1 fuzzy
│   ├── inputoutput.po                    62 /  70 ( 88.0% translated), 7 fuzzy
│   ├── interactive.po                     5 /   7 ( 71.0% translated), 2 fuzzy
│   ├── introduction.po                   68 /  76 ( 89.0% translated), 3 fuzzy
│   ├── modules.po                        69 /  83 ( 83.0% translated), 13 fuzzy
│   ├── stdlib.po                         43 /  46 ( 93.0% translated), 2 fuzzy
│   ├── stdlib2.po                        41 /  45 ( 91.0% translated), 4 fuzzy
│   └── venv.po                           28 /  30 ( 93.0% translated), 2 fuzzy
└── faq/  84.58% done
    ├── design.po                        119 / 143 ( 83.0% translated), 21 fuzzy
    ├── extending.po                      49 /  56 ( 87.0% translated), 6 fuzzy
    ├── general.po                        80 /  97 ( 82.0% translated), 7 fuzzy
    ├── gui.po                            12 /  16 ( 75.0% translated), 3 fuzzy
    ├── library.po                       120 / 133 ( 90.0% translated), 9 fuzzy
    └── programming.po                   355 / 392 ( 90.0% translated), 27 fuzzy
```


### Calculate completion with POT files structure

You can calculate the progress against source (template) files by using `--pot` flag.

```
$ potodo --pot ../cpython/Doc/build/gettext
```


### Handling reservations

To avoid having two translators work on the same file at the same
time, one can tell other translations that a file is being translated
using an issue or a draft pull request.

`potodo` can fetch those issues and display it. It currently work with
Gitea and Github.

For example, in a clone of
[python-docs-fr](https://git.afpy.org/AFPy/python-docs-fr/) you can
run:

```
potodo --api-url 'https://git.afpy.org/api/v1/repos/AFPy/python-docs-fr/issues?state=open' howto/
1 directory  57.73% done
└── howto/  57.73% done
    ├── a-conceptual-overview-of-asyncio.po   4 /  70 (  5.0% translated), reserved by mdk
    ├── annotations.po                    40 /  49 ( 81.0% translated), 5 fuzzy
    ├── argparse-optparse.po              13 /  20 ( 65.0% translated), 1 fuzzy, reserved by mdk
    ├── argparse.po                       77 / 103 ( 74.0% translated), 6 fuzzy
    ├── clinic.po                          1 /   2 ( 50.0% translated)
    ├── cporting.po                        4 /   5 ( 80.0% translated), 1 fuzzy
    ├── curses.po                         86 / 105 ( 81.0% translated), 19 fuzzy
    ├── descriptor.po                    128 / 176 ( 72.0% translated), 46 fuzzy
    ├── enum.po                          152 / 234 ( 64.0% translated), 57 fuzzy
    ├── free-threading-extensions.po       1 / 101 (  0.0% translated), reserved by mdk
    ├── free-threading-python.po           2 /  45 (  4.0% translated), reserved by mdk
    ├── functional.po                    199 / 207 ( 96.0% translated), 8 fuzzy, reserved by Thevenel
    ├── gdb_helpers.po                     1 /  65 (  1.0% translated), reserved by mdk
    ├── index.po                           2 /  30 (  6.0% translated), 1 fuzzy, reserved by Thevenel
    ├── instrumentation.po                53 /  59 ( 89.0% translated), 6 fuzzy
    ├── isolating-extensions.po            2 / 119 (  1.0% translated)
    ├── logging-cookbook.po              184 / 322 ( 57.0% translated), 13 fuzzy
    ├── logging.po                       200 / 222 ( 90.0% translated), 18 fuzzy
    ├── mro.po                             2 /  93 (  2.0% translated)
    ├── perf_profiling.po                  1 /  38 (  2.0% translated)
    ├── pyporting.po                       3 /  13 ( 23.0% translated), 1 fuzzy
    ├── regex.po                         282 / 291 ( 96.0% translated), 5 fuzzy
    ├── remote_debugging.po                3 / 122 (  2.0% translated)
    ├── sorting.po                        36 /  69 ( 52.0% translated), 9 fuzzy, reserved by Thevenel
    ├── timerfd.po                         2 /   9 ( 22.0% translated)
    ├── unicode.po                       119 / 121 ( 98.0% translated), 2 fuzzy
    └── urllib2.po                         5 /  84 (  5.0% translated)
```

For github it would look like `--api-url 'https://api.github.com/repos/ORGANISATION/REPOSITORY/issues?state=open'`.

It's a bit verbose, so maybe hide this in a Makefile or whatever, but
this way you can tweak the parameters of the query, typically to
filter on a label if needed.

The way `potodo` maps issues to files is simple: the path of the file
just has to be present in the issue title, so any issues like:

- `I'm currently working on faq/extending.po`
- `Je travaille sur extending/index.po`
- `blah blah library/functions.po blah blah`

will correctly match their file.


## Development setup

Create a virtual environment:

```sh
python3 -m venv .venv
```

Activate it:

```sh
source .venv/bin/activate
```

Install the dev requirements:

```sh
pip install -e .[dev]
```

Optionally install the pre-commit hooks:

```sh
pre-commit install
```
```


## Release History

* v0.30
  * Subdirectories are now listed in a colored tree-like fashion.
  * Now accepts multiple directories (`-p` flag is now deprecated).
* v0.25
  * Handle gitignore negation by @maciek
  * Base completion on number of words in msgids by @maciek
  * Merge using polib by @maciek
* v0.23.2
  * fix: support CLI for --pot flag by @maciek
* v0.23.1
  * Raise ValueError for empty or not existent POT directory when --pot flag is used by @maciek
* v0.23.0
  * Support basing progress calculations on external file structure (--pot flag) by @maciek
* v0.22.0
  * fix: consider finished files and hide them from output by default by @mattwang44
  * feat: extract po files from all PR to also mark them as reserved by @fviard
  * fix imports pre-commit hook by @maciek
* v0.21.4
  * CI and refactor by @mdk
* v0.21.3
  * Refactor by @mdk
* v0.21.2
    * FIX: Don't miss issues (reservations) to files containing multiple dots. Contributed by @eviau.
* v0.21.0
    * A nice new README
* v0.20.0
    * New exclude behavior with gitignore style matching !
* v0.19.2
    * Dropped `cache_args` to simplify cache functionality
* v0.19.1
    * Fixed a bug of division by 0
    * Replaced Travis-ci tests with github actions
* v0.19.0
    * Fixed windows support
* v0.17.3
    * Fixed a math error where the completion %age of a folder was wrong
    * Fixes on the `.potodoignore` file
* v0.17.0
    * Added tests
    * Fixed bug where github would rate limit your IP address
    * Fixed argument errors
    * Added `-l` `--matching-files` Which will print the path of files matching your arguments
* v0.16.0
    * Args passed to potodo are now cached as well ! This allows for a better control of what is cached !
    * The ignore file now works as the .gitignore does. Add a venv/ in your .potodoignore for example :)
* v0.15.0
    * Potodo now supports .potodoignore files ! You can finally ignore the venv you made 🎉
* v0.14.3
    * Added cache versioning to avoid errors when cache changes, for example if files are moved between `potodo` versions.
* v0.14.2
    * Nothing new, just code moved around ! Thanks for sticking around 🎉
* v0.14.1
    * Added `--only-reserved` option to display only reserved filed
    * Added `--reserved-dates` to display when a file was reserved
    * Added cache to cache `pofiles` to speedup the reading process
    * Added logging for verbosity
    * Added interactive option with `--interactive`
    * Added contributors in the readme
* < v0.14.1
    * Base version

## Contributing

1. Fork it (<https://git.afpy.org/repo/fork/100>)
2. Create your feature branch (`git checkout -b feature/fooBar`

`/!\` Don't forget to bump the version in `potodo/__init__.py` when you're pushing your changes to your branch

3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
