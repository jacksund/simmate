# -*- coding: utf-8 -*-

import logging
import sqlite3

import numpy
import pandas
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column


class ChemblDocument(DatabaseTable):
    """
    This table holds all information about the source documents
    that compound and SAR data was pulled from and into the ChEMBL database.
    """

    class Meta:
        db_table = "chembl__documents"

    published_at = table_column.IntegerField(blank=True, null=True)
    """
    The year when the document was first published
    """

    document_type = table_column.TextField(blank=True, null=True)
    """
    Type of the document (e.g., Publication, Patent, Deposited dataset)
    """

    patent_id = table_column.TextField(blank=True, null=True)
    """
    Patent ID for this document
    """

    doi = table_column.TextField(blank=True, null=True)
    """
	Digital object identifier (DOI) for this reference
    """

    title = table_column.TextField(blank=True, null=True)
    """
    Title of the document
    """

    # BUG: holding off due to unicode issues. See below
    # authors = table_column.JSONField(blank=True, null=True)
    # """
    # List of authors for the document
    # """

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls):
        """
        Loads all document metadata directly from the ChEMBL database into the local
        Simmate database.
        """

        from .molecules import ChemblMolecule

        database_file = ChemblMolecule.download_source_data()
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        logging.info("Pulling document data from ChEMBL db...")
        cursor = connection.cursor()
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

        data = pandas.DataFrame(
            data=cursor.fetchall(),
            columns=[c[0] for c in cursor.description],
        )  # OPTIMIZE: consider fetchmany with for-loop

        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})

        # convert to dictionaries
        data = data.to_dict(orient="records")

        # autopopulate database columns for each molecule (no saving yet)
        logging.info("Generating database objects...")
        failed_rows = []
        for entry in track(data):
            try:
                # now convert the entry to a database object
                cls.objects.update_or_create(
                    id=entry["doc_id"],
                    defaults=dict(
                        published_at=entry["year"],
                        document_type=entry["doc_type"],
                        patent_id=entry["patent_id"],
                        doi=entry["doc_id"],
                        title=entry["title"],
                        # BUG: https://stackoverflow.com/questions/517923/
                        # authors=(
                        #     entry["authors"].split(",") if entry["authors"] else None
                        # ),
                    ),
                )
            except:
                failed_rows.append(entry)

        logging.info("Done!")
        return failed_rows

    @classmethod
    def _download_source_data(
        cls,
        url: str = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/",
        filename: str = "chembl_36_sqlite.tar.gz",
    ):
        pass
