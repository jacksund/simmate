# -*- coding: utf-8 -*-

import logging
import shutil
import sqlite3
from pathlib import Path

import polars

from simmate.config import settings
from simmate.utils import download_file, get_directory


class ChemblClient:

    @staticmethod
    def download_source_data() -> Path:
        """
        Downloads and unpacks the ChEMBL SQLite database.
        """
        target_dir = get_directory(settings.config_directory / "chembl")

        version = 36
        db_name = f"chembl_{version}"
        db_filename = target_dir / f"{db_name}.db"

        if db_filename.exists():
            return db_filename

        base_url = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/"
        filename = f"{db_name}_sqlite.tar.gz"
        download_filename = target_dir / filename

        logging.info("Downloading ChEMBL db...")
        if not download_filename.exists():
            download_file(
                url=base_url + filename,
                dest_path=download_filename,
            )

        logging.info("Unpacking ChEMBL db...")
        shutil.unpack_archive(download_filename, target_dir)
        shutil.move(
            target_dir / db_name / f"{db_name}_sqlite" / db_filename.name,
            target_dir,
        )
        shutil.rmtree(target_dir / db_name)
        download_filename.unlink()

        logging.info("ChEMBL data ready.")
        return db_filename

    @classmethod
    def get_molecule_data(cls, chunk_size: int = 1_000_000):
        """
        Yields chunks of molecule data from the ChEMBL SQLite database as polars DataFrames.
        """
        database_file = cls.download_source_data()
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

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            df = polars.DataFrame(
                data=rows,
                schema=[c[0] for c in cursor.description],
            )
            yield df

    @classmethod
    def get_document_data(cls, chunk_size: int = 1_000_000):
        """
        Yields chunks of document data from the ChEMBL SQLite database as polars DataFrames.
        """
        database_file = cls.download_source_data()
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        logging.info("Pulling document data from ChEMBL db...")
        query = """
            SELECT
              doc_id,
              year,
              doc_type,
              patent_id,
              doi,
              journal,
              title,
              authors
            FROM
              docs
        """
        cursor.execute(query)

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            df = polars.DataFrame(
                data=rows,
                schema=[c[0] for c in cursor.description],
            )
            yield df

    @classmethod
    def get_assay_result_data(
        cls, min_activity_id: int = -1, chunk_size: int = 250_000, limit: int = None
    ):
        """
        Yields chunks of assay result data from the ChEMBL SQLite database as polars DataFrames.
        """
        database_file = cls.download_source_data()
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        logging.info("Pulling assay data from ChEMBL db...")
        query = f"""
            SELECT
              a1.activity_id,
              a1.doc_id,
              a1.molregno,
              a1.standard_relation,
              a1.standard_value,
              a1.standard_units,
              a1.standard_flag,
              a1.standard_type,
              a1.activity_comment,
              a1.data_validity_comment,
              a1.potential_duplicate,
              a1.standard_upper_value,
              a1.standard_text_value,
              a1.action_type,
              a2.description as assay_description,
              a2.assay_organism,
              a2.confidence_score,
              a3.assay_desc as assay_type_description,
              b4.label as bao_type
            FROM
              activities a1
            LEFT JOIN
              assays a2
            	ON
            	a1.assay_id = a2.assay_id
            LEFT JOIN
              assay_type a3
            	ON
            	a2.assay_type = a3.assay_type
            LEFT JOIN
              bioassay_ontology b4
            	ON
            	a2.bao_format = b4.bao_id
            WHERE activity_id > {min_activity_id}
            ORDER BY a1.activity_id
        """
        if limit is not None:
            query += f"\nLIMIT {limit}"

        cursor.execute(query)

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            df = polars.DataFrame(
                data=rows,
                schema=[c[0] for c in cursor.description],
            )
            yield df
