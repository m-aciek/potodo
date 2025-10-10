import sys
import webbrowser
from typing import cast

from simple_term_menu import TerminalMenu

from potodo.po_file import PoDirectories, PoDirectory, PoFileStats

IS_CURSOR_CYCLING = True
IS_SCREEN_CLEARED = True


def _directory_list_menu(directories: list[PoDirectory]) -> PoDirectory:
    dir_list = [directory.path.name for directory in directories]
    dir_list.append("[q] Quit")
    directory_list_menu = TerminalMenu(
        menu_entries=dir_list,
        title="Choose a directory",
        cycle_cursor=IS_CURSOR_CYCLING,
        clear_screen=IS_SCREEN_CLEARED,
        # preview_command="",
        # preview_size=0,
        show_search_hint=True,
        show_shortcut_hints=True,
    )
    selected_directory = directory_list_menu.show()
    try:
        return directories[selected_directory]
    except IndexError:  # That's the [q] Quit
        sys.exit(0)


def _file_list_menu(
    directory: PoDirectory, files: list[PoFileStats]
) -> PoFileStats | None:
    file_list = [file.path.name for file in files]
    file_list.append("[;] Back")
    file_list.append("[q] Quit")
    file_list_menu = TerminalMenu(
        menu_entries=file_list,
        title=f"Choose a file from {directory.path.name}",
        cycle_cursor=IS_CURSOR_CYCLING,
        clear_screen=IS_SCREEN_CLEARED,
        # preview_command="",
        # preview_size=0,
        show_search_hint=True,
        show_shortcut_hints=True,
    )
    index = file_list_menu.show()
    if file_list[index] == "[;] Back":
        return None
    if file_list[index] == "[q] Quit":
        sys.exit(0)
    return files[index]


def _confirmation_menu(choosen_file: PoFileStats, directory: PoDirectory) -> int:
    confimation_menu = TerminalMenu(
        title=f"Are you sure you want to choose {directory.path.name}/{choosen_file.path.name}?"
        f" (This will open a web browser tab to open a new issue)",
        menu_entries=["YES", "NO", "[;] Back", "[q] Quit"],
        cycle_cursor=IS_CURSOR_CYCLING,
        clear_screen=IS_SCREEN_CLEARED,
        show_search_hint=True,
        show_shortcut_hints=True,
    )
    choice = confimation_menu.show()
    return cast(int, choice)


def interactive_output(po_directories: PoDirectories) -> None:
    while True:
        directory = _directory_list_menu(po_directories.subdirectories)
        file_options = sorted(directory.files)
        file = _file_list_menu(directory, file_options)
        if not file:  # User pressed 'back'
            continue
        final_choice = _confirmation_menu(file, directory)
        if final_choice == 3:
            sys.exit(0)
        elif final_choice == 2:
            continue
        else:
            break
    if final_choice == 0:
        webbrowser.open(
            f"https://git.afpy.org/AFPy/python-docs-fr/issues/new?title=Je%20travaille%20sur%20"
            f"{directory.path.name}/{file.path.name}"
            f"&body=%0A%0A%0A---%0AThis+issue+was+created+using+potodo+interactive+mode."
        )
    else:
        sys.exit()
