# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class FingerprintPool(DatabaseTable):
    """
    A table that stores Structure fingerprints

    Interaction with this table is typically done through the fingerprint
    Validator toolkit classes
    """

    class Meta:
        app_label = "core_components"
        # unique_together = ["method", "init_kwargs", "database_table"]

    method = table_column.JSONField(blank=True, null=True)
    """
    The fingerprint validator class used
    """

    init_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The kwargs used to initialized the fingerprint validator class used
    """

    database_table = table_column.CharField(max_length=50, blank=True, null=True)
    """
    The database table that structures are being pulled from. 
    
    We require this to be set to a single table because the id of each 
    Fingerprint should match the id of the structure it came from. Note, 
    this is not a relation to the Structure table because its an abstract model.
    """


class Fingerprint(DatabaseTable):
    """
    A table that stores Structure fingerprints

    Interaction with this table is typically done through the fingerprint
    Validator toolkit classes
    """

    class Meta:
        app_label = "core_components"

    database_id = table_column.IntegerField(blank=True, null=True)
    """
    The id of the structure that this fingerprint came from
    """

    fingerprint = table_column.JSONField(blank=True, null=True)
    """
    The resulting fingerprint. This is typically a 1D array.
    """

    pool = table_column.ForeignKey(
        FingerprintPool,
        on_delete=table_column.CASCADE,
        related_name="fingerprints",
        blank=True,
        null=True,
    )
    """
    The database pool that this fingerprint belongs to. The pool contians useful
    information such as the fingerprint method, kwargs used, and the table that
    structures are being pulled from.
    """

    @property
    def source(self):
        # NOTE: The id of this fingerprint should match the id of the structure
        # it came from.
        return {
            "database_table": self.pool.database_table,
            "database_id": self.database_id,
        }
