# -*- coding: utf-8 -*-

import contextlib
import logging
import urllib.request
import warnings
import zipfile
from pathlib import Path

from pymatgen.io.cif import CifParser
from rich.progress import track

from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import Structure, ThirdPartyData
from simmate.database.utils import batch_bulk_create


class CodStructure(ThirdPartyData, Structure):
    """
    Crystal structures from the [COD](https://www.crystallography.net/cod/) database.

    Currently, this table only stores the strucure, plus comments on whether the
    sturcture is ordered or has implicit hydrogens.
    """

    class Meta:
        db_table = "cod__structures"

    # -------------------------------------------------------------------------

    external_website = "https://www.crystallography.net/cod/"
    source_doi = "https://doi.org/10.1107/S0021889809016690"
    is_redistribution_allowed = True

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the COD website.
        """
        # All COD structures have their data mapped to a URL in the same way
        # ex: https://www.crystallography.net/cod/12345.html"
        return f"https://www.crystallography.net/cod/{self.id}.html"

    # -------------------------------------------------------------------------

    remote_archive_link = (
        "https://assets.simmate.org/cod/archive/CodStructure-minimal-2026-08-17.csv.zip"
    )
    archive_fields = ["is_ordered", "has_implicit_hydrogens"]

    # -------------------------------------------------------------------------

    is_ordered = table_column.BooleanField(blank=True, null=True)
    """
    whether the structure contains disordered sites (i.e. mixed occupancies)
    """

    has_implicit_hydrogens = table_column.BooleanField(blank=True, null=True)
    """
    whether the structure has implicit Hydrogens. This means there should be
    Hydrogens in the structure, but they weren't explicitly drawn. Note,
    implicit hydrogens will make the chemical system and formula misleading 
    because of the absence of hydrogens.
    """

    # -------------------------------------------------------------------------

    @classmethod
    @batch_bulk_create(batch_size=1_000)
    def load_source_data(
        cls,
        base_directory: str | Path = None,
        only_add_new_cifs: bool = True,
    ):
        """This method pulls COD data into the Simmate database."""

        base_directory = Path(
            base_directory or settings.config_directory / "cod" / "raw"
        )
        base_directory.mkdir(parents=True, exist_ok=True)

        filename = "cod-rev297631-2025.02.07.zip"
        file_path = base_directory / filename

        cif_files = list(base_directory.rglob("*.cif"))

        # Download zip if no CIFs are present and zip doesn't exist
        if not cif_files and not file_path.exists():
            logging.info(f"Downloading {filename}...")
            url = f"https://www.crystallography.net/archives/2025/data/{filename}"
            try:
                urllib.request.urlretrieve(url, file_path)
            except Exception as e:
                raise Exception(
                    f"Failed to download {filename}. Please manually download it "
                    f"from {url} "
                    f"to {base_directory}.\nError: {e}"
                )

        existing_ids = (
            set(cls.objects.values_list("id", flat=True))
            if only_add_new_cifs
            else set()
        )

        with contextlib.ExitStack() as stack, warnings.catch_warnings():
            warnings.simplefilter("ignore")

            targets = []
            if cif_files:
                for path in cif_files:
                    cif_id = int(path.stem)
                    if cif_id not in existing_ids:
                        targets.append((cif_id, path))
            else:
                z = stack.enter_context(zipfile.ZipFile(file_path))
                for info in z.infolist():
                    if info.filename.endswith(".cif"):
                        cif_id = int(Path(info.filename).stem)
                        if cif_id not in existing_ids:
                            targets.append((cif_id, info))

            logging.info(f"Adding {len(targets)} new entries...")

            for cif_id, target in track(targets, description="Parsing CIFs..."):
                try:
                    cif_string = (
                        target.read_text()
                        if isinstance(target, Path)
                        else z.read(target).decode("utf-8")
                    )
                    yield cls._from_cif(cif_string=cif_string, cif_id=cif_id)
                except Exception:
                    logging.warning(f"Failed to parse CIF: {cif_id}")

    @classmethod
    def _from_cif(cls, cif_string: str, cif_id: int):
        """Converts a COD cif into a Simmate database object."""
        try:
            cif = CifParser.from_str(cif_string, occupancy_tolerance=float("inf"))
            structure = cif.get_structures()[0]

            # Mark overly complex structures as invalid to avoid database blowup
            if (
                len(structure) > 500
                or len(structure.composition.chemical_system) > 25
                or len(structure.composition.formula) > 50
                or len(structure.composition.reduced_formula) > 50
                or len(structure.composition.anonymized_formula) > 50
            ):
                raise ValueError("Structure too complex")

            return cls.from_toolkit(
                id=cif_id,
                structure=structure,
                is_ordered=structure.is_ordered,
                has_implicit_hydrogens=(
                    "Structure has implicit hydrogens defined" in "".join(cif.warnings)
                ),
                is_invalid_structure=False,
            )
        except Exception:
            return cls.from_toolkit(
                id=cif_id,
                structure=None,
                is_ordered=None,
                has_implicit_hydrogens=None,
                is_invalid_structure=True,
            )
