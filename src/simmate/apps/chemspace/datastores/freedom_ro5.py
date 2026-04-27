# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from simmate.toolkit.datastores import MoleculeStore

from ..client import ChemspaceClient


class FreedomRo5MoleculeStore(MoleculeStore):
    """
    MoleculeStore for the ChemSpace Freedom Rule-of-5 dataset.
    """

    app_name = "chemspace"
    datastore_name = "freedom/rule_of_5"
    chunk_size = 1_000_000
    smiles_stored = "original_only"

    metadata_columns = [
        "id",
        "reaction_id",
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
        reorganize: bool = True,
        parallel_job: bool = False,
        parallel_core: bool = False,
    ):
        """
        Loads molecule data from ChemSpace source files into the MoleculeStore.

        Args:
            source_directory (str | Path, optional): The directory where the
                ChemSpace source files are located. If None, it will be
                downloaded using ChemspaceClient.
            target_directory (str | Path, optional): The directory where the
                MoleculeStore is located. If None, it will use the default.
            reorganize (bool, optional): Whether to reorganize chunks after
                loading. Defaults to True.
            parallel (bool, optional): Whether to submit worker jobs to load
                ChemSpace data in parallel. Defaults to True.
        """
        if not source_directory:
            source_directory = ChemspaceClient.download_source_data()

        source_directory = Path(source_directory)
        files = (
            [source_directory]
            if source_directory.is_file()
            else list(source_directory.rglob("*.bz2"))
        )

        if parallel_job:

            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor

            logging.info(f"Submitting {len(files)} jobs to the queue...")
            for file in files:
                SimmateExecutor.submit(
                    cls._load_single_source,
                    source_directory=file,
                    target_directory=target_directory,
                    parallel=parallel_core,
                    tags=["load-chembl-datastore"],
                )
            if reorganize:
                logging.info(
                    "Jobs submitted. Run reorganize_chunks() after completion."
                )

        else:
            for file in files:
                logging.info(f"Loading {file}...")
                cls._load_single_source(file, target_directory, parallel=parallel_core)
            if reorganize:
                logging.info("Reorganizing chunks...")
                cls.reorganize_chunks(target_directory=target_directory)

            logging.info("Done loading ChemSpace data.")

    @classmethod
    def _load_single_source(
        cls,
        source_directory: str | Path,
        target_directory: str | Path = None,
        parallel: bool = False,
    ):
        """
        Worker method to load a single ChemSpace file into the MoleculeStore.
        """
        for df in ChemspaceClient.get_freedom_ro5_data(source_dir=source_directory):
            df = df.rename({"ID": "id", "SMILES": "smiles"})
            cls.add_dataframe(df, target_directory=target_directory, parallel=parallel)
