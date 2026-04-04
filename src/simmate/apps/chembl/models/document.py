# -*- coding: utf-8 -*-

from simmate.database.core import DatabaseTable, table_column
from simmate.database.utils import batch_bulk_create

from ..client import ChemblClient


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

    # BUG: holding off due to unicode issues
    # authors = table_column.JSONField(blank=True, null=True)
    # """
    # List of authors for the document
    # """

    @classmethod
    @batch_bulk_create(batch_size=10_000)
    def load_source_data(cls, **kwargs):
        for df in ChemblClient.get_document_data(chunk_size=10_000):
            for row in df.iter_rows(named=True):
                yield cls(
                    id=row["doc_id"],
                    published_at=row["year"],
                    document_type=row["doc_type"],
                    patent_id=row["patent_id"],
                    doi=row["doi"],
                    title=row["title"],
                )
