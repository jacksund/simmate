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
    def _load_data(cls, source_directory: str | Path = None):
        """
        Loads data from the ChEMBL SQLite database into the MoleculeStore.
        """
        import sqlite3
        import pandas
        from simmate.apps.chembl.models import ChemblMolecule

        database_file = ChemblMolecule.download_source_data()
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        logging.info("Pulling molecule data from ChEMBL db...")
        query = """
        SELECT
            S1.molregno,
            S1.canonical_smiles,
         	D1.chembl_id,
            D1.molecule_type,
            P1.qed_weighted,
            P1.alogp,
            P1.ro3_pass,
            P1.num_ro5_violations,
            P1.hba,
            P1.hbd,
            P1.np_likeness_score
        FROM
         	compound_structures S1
        LEFT JOIN 
        	molecule_dictionary D1
        	ON S1.molregno = D1.molregno
        LEFT JOIN 
        	compound_properties P1
        	ON S1.molregno = P1.molregno
        ORDER BY
            S1.molregno ASC
        """
        cursor.execute(query)

        # We load in chunks to avoid memory issues with the full ChEMBL dataset
        while True:
            rows = cursor.fetchmany(cls.chunk_size)
            if not rows:
                break
            
            logging.info(f"Processing chunk of {len(rows)} molecules...")
            
            df = pandas.DataFrame(
                data=rows,
                columns=[c[0] for c in cursor.description],
            )

            # Convert to polars and rename columns to match MoleculeStore expectations
            df_polars = polars.from_pandas(df)
            df_polars = df_polars.rename({
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

            # RO3 is given as Y, N, or (NULL) -- but we want a boolean
            # We do this mapping in polars
            df_polars = df_polars.with_columns(
                polars.col("rule_of_3_pass").map_elements(
                    lambda x: True if x == "Y" else (False if x == "N" else None),
                    return_dtype=polars.Boolean,
                )
            )

            cls.add_dataframe(df_polars)

        logging.info("Done loading ChEMBL data into MoleculeStore.")
