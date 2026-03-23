# -*- coding: utf-8 -*-

import logging
import sqlite3

import numpy
import pandas
from rich.progress import track

from simmate.database.core import DatabaseTable, table_column


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

        # autopopulate database columns for each molecule (no saving yet)
        logging.info("Generating database objects and saving in batches...")
        failed_rows = []
        db_objs = []
        for i, entry in track(data.iterrows(), total=len(data)):
            try:
                # now convert the entry to a database object
                new_obj = cls(
                    id=entry["doc_id"],
                    published_at=entry["year"],
                    document_type=entry["doc_type"],
                    patent_id=entry["patent_id"],
                    doi=entry["doi"],
                    title=entry["title"],
                    # BUG: https://stackoverflow.com/questions/517923/
                    # authors=(
                    #     entry["authors"].split(",") if entry["authors"] else None
                    # ),
                )
                db_objs.append(new_obj)
            except:
                failed_rows.append(entry.to_dict())

            # save every time we have 1000 structures
            if len(db_objs) >= 1000:
                cls.objects.bulk_create(
                    db_objs,
                    batch_size=1000,
                    ignore_conflicts=True,
                )
                db_objs = []  # reset for next batch

        # one last save in case we exited the loop above with
        # remaining structures
        if db_objs:
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
            )

        logging.info("Done!")
        return failed_rows

    @classmethod
    def _download_source_data(
        cls,
        url: str = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/",
        filename: str = "chembl_36_sqlite.tar.gz",
    ):
        pass
