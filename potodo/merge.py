import logging
import shutil
from pathlib import Path

import polib


def sync_po_and_pot(po_dirs: list[Path], pot_dir: Path, output_dir: Path) -> None:
    if not pot_dir.exists():
        raise ValueError(f"POT directory {pot_dir} doesn't exist")
    if not any(pot_dir.rglob("*.pot")):
        raise ValueError(f"POT directory {pot_dir} doesn't contain any POT file")

    processed_pots = set()

    for po_dir in po_dirs:
        for po_path in po_dir.rglob("*.po"):
            relative_path = po_path.relative_to(po_dir)
            pot_path = pot_dir / relative_path.with_suffix(".pot")
            output_po_path = output_dir / relative_path

            if pot_path.exists():
                processed_pots.add(pot_path)

                output_po_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    file = polib.pofile(po_path)
                except IOError:
                    shutil.copy(pot_path, output_po_path)
                    logging.exception(
                        "Error merging %s. Replaced with %s", po_path, pot_path
                    )
                else:
                    file.merge(polib.pofile(pot_path))
                    file.save(str(output_po_path))
                    logging.debug(
                        "Merged %s with %s -> %s", po_path, pot_path, output_po_path
                    )

    for pot_path in pot_dir.rglob("*.pot"):
        if pot_path not in processed_pots:
            relative_path = pot_path.relative_to(pot_dir)
            output_po_path = output_dir / relative_path.with_suffix(".po")

            output_po_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(pot_path, output_po_path)
            logging.debug(
                "No matching PO for %s. Moved to %s as .po.", pot_path, output_po_path
            )
