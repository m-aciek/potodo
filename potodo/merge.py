import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Union


def sync_po_and_pot(po_dir: Path, pot_dir: Path, output_dir: Path) -> None:
    if not pot_dir.exists():
        raise ValueError(f"POT directory {pot_dir} doesn't exist")
    if not any(pot_dir.rglob("*.pot")):
        raise ValueError(f"POT directory {pot_dir} doesn't contain any POT file")

    processed_pots = set()

    for po_path in po_dir.rglob("*.po"):
        relative_path = po_path.relative_to(po_dir)
        pot_path = pot_dir / relative_path.with_suffix(".pot")
        output_po_path = output_dir / relative_path

        if pot_path.exists():
            processed_pots.add(pot_path)

            output_po_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                subprocess.run(
                    [
                        get_msgmerge_command(),
                        "--no-fuzzy-matching",
                        po_path,
                        pot_path,
                        "-o",
                        output_po_path,
                    ],
                    check=True,
                )
                logging.debug(f"Merged {po_path} with {pot_path} -> {output_po_path}")
            except subprocess.CalledProcessError:
                shutil.copy(pot_path, output_po_path)
                logging.debug(f"Error merging {po_path}. Replaced with {pot_path}")
            except OSError as e:
                raise OSError("GNU gettext is required for --pot flag to run") from e

    for pot_path in pot_dir.rglob("*.pot"):
        if pot_path not in processed_pots:
            relative_path = pot_path.relative_to(pot_dir)
            output_po_path = output_dir / relative_path.with_suffix(".po")

            output_po_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(pot_path, output_po_path)
            logging.debug(
                f"No matching PO for {pot_path}. Moved to {output_po_path} as .po."
            )


def get_msgmerge_command() -> Union[str, Path]:
    if platform.system() == "Windows":
        return Path("C:/gettext/bin/msgmerge.exe")
    return "msgmerge"
