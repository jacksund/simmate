# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class Fingerprint(DatabaseTable):
    """
    A table that stores Structure fingerprints

    Interaction with this table is typically done through the fingerprint
    Validator toolkit classes
    """

    class Meta:
        app_label = "core_components"

    method = table_column.JSONField(blank=True, null=True)
    """
    The fingerprint validator class used
    """

    init_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The kwargs used to initialized the fingerprint validator class used
    """

    fingerprint = table_column.JSONField(blank=True, null=True)
    """
    The resulting fingerprint. This is typically a 1D array.
    """

    # note: the structure that was used to generate the fingerprint will
    # be stored in the "source" column
