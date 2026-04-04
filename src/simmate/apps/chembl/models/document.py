# -*- coding: utf-8 -*-

import logging

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
        from simmate.apps.chembl.client import ChemblClient

        logging.info("Generating database objects and saving in batches...")
        failed_rows = []
        for df in ChemblClient.get_document_data(chunk_size=10_000):

            db_objs = []
            for entry in track(df.iter_rows(named=True), total=len(df)):
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
                    failed_rows.append(entry)

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
