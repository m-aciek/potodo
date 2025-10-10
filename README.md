<p align="center">
    <img width=60% src="https://git.afpy.org/AFPy/potodo/raw/branch/main/media/Potodo.png">
</p>
<p align="center">
    <a href="https://woodpecker.afpy.org/AFPy/potodo"><img src="https://woodpecker.afpy.org/api/badges/AFPy/potodo/status.svg"></a>
    <img src="https://img.shields.io/pypi/v/potodo?color=green">
    <img src="https://img.shields.io/badge/python-v3.7+-green.svg">
    <img src="https://img.shields.io/badge/license-MIT-green.svg">
</p>

## What is it ?

Potodo, a (almost) flawless TODO/progress listing CLI tool for po files.

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
$ potodo --exclude venv .venv whatsnew c-api/ distutils/

# python-docs-fr (95.31% done)

- bugs.po                         29 /  30 ( 96.0% translated).
- copyright.po                     6 /   7 ( 85.0% translated), 1 fuzzy.
- license.po                      87 /  91 ( 95.0% translated), 2 fuzzy.


# extending (56.81% done)

- building.po                     22 /  23 ( 95.0% translated), 1 fuzzy.
- extending.po                   120 / 158 ( 75.0% translated), 8 fuzzy.
- index.po                        11 /  12 ( 91.0% translated), 1 fuzzy.
- newtypes.po                     38 /  89 ( 42.0% translated), 3 fuzzy.
- newtypes_tutorial.po            31 / 123 ( 25.0% translated), 2 fuzzy.
- windows.po                      20 /  21 ( 95.0% translated), 1 fuzzy.

[...]

# TOTAL (50.01% done)
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
$ potodo --api-url 'https://git.afpy.org/api/v1/repos/AFPy/python-docs-fr/issues?state=open&type=issues' --exclude .venv
[...]
# extending (56.81% done)

- building.po                     22 /  23 ( 95.0% translated), 1 fuzzy, reserved by Starmania.
- extending.po                   120 / 158 ( 75.0% translated), 8 fuzzy.
- index.po                        11 /  12 ( 91.0% translated), 1 fuzzy.
- newtypes.po                     38 /  89 ( 42.0% translated), 3 fuzzy.
- newtypes_tutorial.po            31 / 123 ( 25.0% translated), 2 fuzzy.
- windows.po                      20 /  21 ( 95.0% translated), 1 fuzzy.


# faq (90.88% done)

- extending.po                    55 /  58 ( 94.0% translated), 3 fuzzy.
- general.po                      88 /  98 ( 89.0% translated).
- gui.po                          16 /  17 ( 94.0% translated), 1 fuzzy, reserved by Iucounu.
- library.po                     139 / 140 ( 99.0% translated).
- programming.po                 340 / 389 ( 87.0% translated), 40 fuzzy.
[...]
```

Notice the **reserved by** column.

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

Create a virtual environment
```sh
python3 -m venv venv
```

Activate it
```sh
source venv/bin/activate
```

Install the dev requirements
```sh
pip install -r requirements-dev.txt
```

Install the pre-commit hook
```sh
pre-commit install
```

Install `potodo` in a development version
```
pip install -e .
```

## Release History

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
