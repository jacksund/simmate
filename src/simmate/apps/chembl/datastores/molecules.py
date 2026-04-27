# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores import MoleculeStore

from ..client import ChemblClient


class ChemblMoleculeStore(MoleculeStore):
    """
    A MoleculeStore for the ChEMBL database, providing optimized search
    and retrieval of bioactive molecules.
    """

    app_name = "chembl"
    datastore_name = "molecules"
    metadata_columns = [
        "id",
        "chembl_id",
        "molecule_type",
        "drug_likeness",
        "alog_p_chembl",
        "rule_of_3_pass",
        "rule_of_5_violations",
        "num_h_acceptors_lipinski",
        "num_h_donors_lipinski",
        "natural_product_likeness",
    ]

    @classmethod
    def load_source_data(
        cls,
        source_directory: str | Path = None,
        target_directory: str | Path = None,
        reorganize: bool = True,
    ):
        """
        Downloads the ChEMBL SQLite database and loads molecule data into the
        MoleculeStore.

        Args:
            source_directory (str | Path, optional): The directory where the
                ChEMBL SQLite database is located. If None, it will be
                downloaded using ChemblClient.
            target_directory (str | Path, optional): The directory where the
                MoleculeStore is located. If None, it will use the default.
            reorganize (bool, optional): Whether to reorganize chunks after
                loading. Defaults to True.
        """
        logging.info("Pulling molecule data from ChEMBL db into MoleculeStore...")

        for df in ChemblClient.get_molecule_data(
            chunk_size=cls.chunk_size,
            source_directory=source_directory,
        ):
            df_polars = df.rename(
                {
                    "molregno": "id",
                    "canonical_smiles": "smiles",
                    "qed_weighted": "drug_likeness",
                    "alogp": "alog_p_chembl",
                    "ro3_pass": "rule_of_3_pass",
                    "num_ro5_violations": "rule_of_5_violations",
                    "hba": "num_h_acceptors_lipinski",
                    "hbd": "num_h_donors_lipinski",
                    "np_likeness_score": "natural_product_likeness",
                }
            )

            df_polars = df_polars.with_columns(
                polars.col("rule_of_3_pass").map_elements(
                    lambda x: True if x == "Y" else (False if x == "N" else None),
                    return_dtype=polars.Boolean,
                )
            )

            cls.add_dataframe(
                df_polars,
                target_directory=target_directory,
            )

        if reorganize:
            logging.info("Reorganizing chunks...")
            cls.reorganize_chunks(target_directory=target_directory)

        logging.info("Done loading ChEMBL data into MoleculeStore.")
