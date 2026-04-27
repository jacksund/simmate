# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from simmate.toolkit.datastores import MoleculeStore

from ..client import ChemspaceClient


class Chemspace_Freedom_Ro5_MoleculeStore(MoleculeStore):
    app_name = "chemspace"
    datastore_name = "freedom/rule_of_5"
    chunk_size = 1_000_000
    smiles_stored = "original_only"
    metadata_columns = [
        "id",
        "reaction_id",
        # "SMILES",
        # others from original dataset:
        "Components",  # number of elements
        "MW",
        "HAC",
        "LogP",
        "HBA",
        "HBD",
        "RotBonds",
        "FSP3",
        "TPSA",
        "InChIKey",
    ]
    property_columns = []
    morgan_fingerprint_cache = False
    pattern_fingerprint_cache = False

    @classmethod
    def load_source_data(
        cls,
        source_directory: str | Path = None,
        target_directory: str | Path = None,
    ):
        logging.info("Pulling ChemSpace Freedom Ro5 data into MoleculeStore...")
        for df in ChemspaceClient.get_freedom_ro5_data(source_dir=source_directory):
            df = df.rename({"ID": "id", "SMILES": "smiles"})
            cls.add_dataframe(df, target_directory=target_directory)
        logging.info("Done loading ChemSpace data.")
