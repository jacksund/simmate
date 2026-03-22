# -*- coding: utf-8 -*-

import logging
import warnings
from pathlib import Path

from pymatgen.io.cif import CifParser
from rich.progress import track

from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import Structure, ThirdPartyData
from simmate.utilities.other import chunk_list


class CodStructure(ThirdPartyData, Structure):
    """
    Crystal structures from the [COD](https://www.crystallography.net/cod/) database.

    Currently, this table only stores the strucure, plus comments on whether the
    sturcture is ordered or has implicit hydrogens.
    """

    class Meta:
        db_table = "cod__structures"

    # -------------------------------------------------------------------------

    html_display_name = "COD"
    html_description_short = (
        "The Crystallography Open Database (COD) is an open-access collection "
        "of crystal structures for organic, inorganic, metal-organic compounds, "
        "and minerals. It serves as a primary resource for experimental "
        "diffraction data."
    )

    html_entries_template = "cod/structures/table.html"
    html_entry_template = "cod/structures/view.html"

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

    remote_archive_link = "https://archives.simmate.org/CodStructure-2026-03-20.zip"
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
    def load_source_data(
        cls,
        base_directory: str | Path = None,
        only_add_new_cifs: bool = True,
        chunk_size: int = 5000,
    ):
        """
        This method pulls COD data into the Simmate database.
        """

        # 1. Determine the base directory
        if not base_directory:
            cod_dir = settings.config_directory / "cod"
            potential_dirs = sorted([d for d in cod_dir.glob("cod-*") if d.is_dir()])
            base_directory = (
                (potential_dirs[-1] / "cif")
                if potential_dirs
                else (Path.cwd() / "cod" / "cif")
            )

        base_directory = Path(base_directory)
        if not base_directory.exists():
            raise FileNotFoundError(f"COD data not found at {base_directory}")

        # 2. Gather all CIF files
        logging.info(f"Gathering CIF files from {base_directory}...")
        all_cifs = list(base_directory.rglob("*.cif"))

        # 3. Filter for new entries if requested
        if only_add_new_cifs:
            logging.info("Filtering for new entries...")
            existing_ids = set(cls.objects.values_list("id", flat=True))
            all_cifs = [f for f in track(all_cifs) if int(f.stem) not in existing_ids]
            logging.info(f"Adding {len(all_cifs)} new entries...")

        # 4. Run the import in chunks
        nchunks_total = (len(all_cifs) // chunk_size) + 1

        # we want to suppress the overwhelming amount of warnings that the
        # CifParser and from_toolkit prints out.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            for i, cif_chunk in enumerate(chunk_list(all_cifs, chunk_size)):
                logging.info(f"Processing chunk {i+1} of {nchunks_total}...")
                db_objs = []
                for cif_file in track(cif_chunk):
                    try:
                        db_obj = cls._from_cif(cif_file)
                        db_objs.append(db_obj)
                    except Exception:
                        logging.warning(f"Failed to parse CIF: {cif_file}")

                logging.info(f"Saving {len(db_objs)} objects to database...")
                cls.objects.bulk_create(
                    db_objs,
                    batch_size=1000,
                    ignore_conflicts=True,
                )

    @classmethod
    def _from_cif(cls, cif_filepath: str | Path):
        """
        Converts a COD cif into a Simmate database object.
        """

        cif_path = Path(cif_filepath)

        try:
            cif = CifParser(cif_path, occupancy_tolerance=float("inf"))
            structure = cif.get_structures()[0]
            # Mark overly complex structures as invalid to avoid database blowup
            if len(structure) > 500 or len(structure.composition) > 10:
                raise ValueError("Structure too complex")
            is_invalid_structure = False
        except Exception:
            structure = None
            is_invalid_structure = True

        has_implicit_hydrogens = (
            "Structure has implicit hydrogens defined" in "".join(cif.warnings)
            if structure
            else None
        )
        is_ordered = structure.is_ordered if structure else None

        # Convert the entry to a database object
        structure_db = cls.from_toolkit(
            id=int(cif_path.stem),
            structure=structure,
            is_ordered=is_ordered,
            has_implicit_hydrogens=has_implicit_hydrogens,
            is_invalid_structure=is_invalid_structure,
        )
        return structure_db
