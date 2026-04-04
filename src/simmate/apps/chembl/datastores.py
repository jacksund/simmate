# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores import MoleculeStore


class ChemblMoleculeStore(MoleculeStore):

    directory_name = "chembl"
    chunk_size = 1_000_000
    smiles_stored = "original_and_cleaned"
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
    property_columns = [
        "molecular_weight_exact",
        "num_atoms_heavy",
        "num_rings",
        "log_p_rdkit",
        "synthetic_accessibility",
    ]
    morgan_fingerprint_cache = False
    pattern_fingerprint_cache = True

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls, source_directory: str | Path = None):
        """
        Loads data from the ChEMBL SQLite database into the MoleculeStore.
        """
        from simmate.apps.chembl.client import ChemblClient

        logging.info("Pulling molecule data from ChEMBL db into MoleculeStore...")
        for df in ChemblClient.get_molecule_data(chunk_size=cls.chunk_size):
            
            df_polars = df.rename({
                "molregno": "id",
                "canonical_smiles": "smiles",
                "qed_weighted": "drug_likeness",
                "alogp": "alog_p_chembl",
                "ro3_pass": "rule_of_3_pass",
                "num_ro5_violations": "rule_of_5_violations",
                "hba": "num_h_acceptors_lipinski",
                "hbd": "num_h_donors_lipinski",
                "np_likeness_score": "natural_product_likeness",
            })
            
            df_polars = df_polars.with_columns(
                polars.col("rule_of_3_pass").map_elements(
                    lambda x: True if x == "Y" else (False if x == "N" else None),
                    return_dtype=polars.Boolean,
                )
            )
            
            cls.add_dataframe(df_polars)

        logging.info("Done loading ChEMBL data into MoleculeStore.")
