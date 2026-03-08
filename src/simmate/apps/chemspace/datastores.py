# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores import MoleculeStore


class Chemspace_Freedom_Ro5_MoleculeStore(MoleculeStore):

    directory_name = "chemspace/freedom/rule_of_5"
    chunk_size = 1_000_000
    smiles_stored = "original_only"
    metadata_columns = [
        "id",
        "reaction_id",
        "SMILES",
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

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls, source_directory: str | Path):
        # should use the output dir from .utilities.download_raw_files
        source_directory = Path(source_directory)
        all_files = [p for p in source_directory.rglob("*.bz2") if p.is_file()]
        for i, file in enumerate(all_files):
            logging.info(f"Adding file {i+1} of {len(all_files)}")
            with bz2.open(file, "rb") as f_in:
                file_content = f_in.read()
                df = polars.read_csv(file_content, separator="\t")
                df = df.rename({"ID": "id", "SMILES": "smiles"})
                cls.add_dataframe(df)
