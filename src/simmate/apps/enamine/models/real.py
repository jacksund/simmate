# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import pandas
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.toolkit.file_converters import SmilesAdapter


class EnamineRealMolecule(Molecule):
    """
    Molecules from the [Enamine REAL](https://enamine.net/) database.
    """

    class Meta:
        db_table = "enamine__real__molecules"

    # disable cols
    source = None

    html_display_name = "Enamine REAL"
    html_description_short = (
        "The largest enumerated database of synthetically feasible molecules"
    )
    is_redistribution_allowed = False

    external_website = (
        "https://enamine.net/compound-collections/real-compounds/real-database"
    )

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the molecule 
    
    ex: "Z4184403259" or "PV-002887495120"
    """

    smiles_type = table_column.CharField(blank=True, null=True, max_length=5)
    """
    Honestly... Not sure what this entry means because everything I see is
    labeled "M", which I assume just means molecule.
    """

    is_diverse_subset = table_column.BooleanField(
        blank=True,
        null=True,
        db_index=True,
    )
    """
    Whether this entry is part of "diverse" subset of the Enamine REAL
    dataset. The full subset is ~50 million molecules
    """

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the Enamine website.
        """
        # !!! as far as I know, there isn't a URL endpoint for each entry
        return "#"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(
        cls,
        input_file: str | Path = "Enamine_Diverse_REAL_drug-like_48.2M.cxsmiles",
        chunk_file: bool = False,
    ):
        """
        Loads all structures directly for the eMolecules database into the local
        Simmate database.

        Enamine distributes their database as manual downloads from
        [here](https://enamine.net/compound-collections/real-compounds/real-database).
        We use the cxsmiles file as input.
        """

        # The SDF file is too large to load, so we split it into chunks first
        if chunk_file:
            logging.info("Splitting cxSmiles file into chunks...")
            chunk_filenames = SmilesAdapter.split_smi_file(
                filename=input_file,
                chunk_size=10000,
                has_headers=True,
            )
            nchunks = len(chunk_filenames)
            logging.info(f"Made {nchunks} total chunks of 10k molecules each.")
        else:
            chunk_filenames = [Path(input_file)]  # we only have the one file to act on
            nchunks = 1

        # go through each chunk and load into the database
        logging.info("The progress bars below are for EACH chunk.")
        logging.info("Saving to simmate database...")

        for i, chunk_filename in enumerate(chunk_filenames):
            logging.info(f"Chunk {i+1} of {nchunks}")

            # read the file text (without loading as Molecule objects)
            data = pandas.read_csv(chunk_filename, delimiter="\t")

            # autopopulate database columns for each molecule (no saving yet)
            logging.info("Generating database objects...")
            failed_rows = []
            db_objs = []
            for i, entry in track(data.iterrows(), total=len(data)):
                try:
                    molecule = ToolkitMolecule.from_smiles(entry.smiles)

                    # now convert the entry to a database object
                    molecule_db = cls.from_toolkit(
                        id=entry.idnumber,
                        smiles_type=entry.Type,
                        molecule=molecule,
                        molecule_original=entry.smiles,
                        is_diverse_subset=True,  # I haven't looked at the full set yet
                    )
                    db_objs.append(molecule_db)
                except:
                    failed_rows.append(entry)
            # save each entry to simmate database
            logging.info("Saving to Simmate database...")
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
            )

            logging.info("Adding molecule fingerprints...")
            cls.populate_fingerprint_database()

            # delete the file if successful AND if chunking was requested
            if chunk_file:
                chunk_filename.unlink()

        logging.info("Done!")
        return failed_rows
