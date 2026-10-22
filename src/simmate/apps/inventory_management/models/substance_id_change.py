from simmate.database.core import DatabaseTable, table_column


class SubstanceIdChange(DatabaseTable):
    """
    An append-only log of changes to substance IDs, such as merges, promotions,
    and splits.

    Substance IDs are meant to be permanent, but our uniqueness checks will
    keep improving over time (e.g. better tautomer or stereochem handling),
    which means substances will occasionally need to be merged or split. IDs
    can also be promoted to a lower level (e.g. a virtual level 2 compound is
    synthesized and becomes level 1), which changes the ID itself.

    Each row is a single "edge" from an old ID to a new ID, so a merge of 3
    substances into 1 gives 2 rows and a split of 1 substance into 3 gives 3
    rows. Retired substances stay in the `Substance` table as tombstones
    (`is_delisted=True`) with `replaced_by` pointing to their current
    successor, while this table keeps the full history of when and why each
    change was made.

    IDs are stored as plain text (not foreign keys) so that this log can also
    record changes for IDs that only exist in the `SubstanceDatastore`.

    Use the methods on `Substance` (e.g. `Substance.merge`) to make changes,
    which update all linked tables and write to this log in one transaction.
    """

    class Meta:
        db_table = "inventory_management__substance_id_changes"

    # -------------------------------------------------------------------------

    change_type_options = [
        "merge",  # old_id was a duplicate of new_id and now redirects to it
        "promote",  # old_id was moved to a new ID at a different level
        "split",  # new_id was created from part of old_id (old_id is kept)
        "redefine",  # the structure of old_id was corrected (no new_id)
        "delist",  # old_id was removed from the catalog (no new_id)
        "reparent",  # the parent of old_id was changed to new_id
    ]
    change_type = table_column.CharField(max_length=10)
    """
    The kind of change made. Must be one of `change_type_options`.
    """

    old_id = table_column.CharField(max_length=12, db_index=True)
    """
    The substance ID that was changed.
    """

    new_id = table_column.CharField(
        max_length=12,
        blank=True,
        null=True,
        db_index=True,
    )
    """
    The substance ID that `old_id` was changed to (if any).
    """

    reason = table_column.TextField(blank=True, null=True)
    """
    A description of why the change was made.
    """

    matching_version = table_column.CharField(max_length=25, blank=True, null=True)
    """
    The version of the uniqueness/matching rules that led to this change
    (if any). This allows changes to be traced back to (and potentially
    reverted for) a specific update to `Substance.register_molecules`.
    """

    extra_metadata = table_column.JSONField(blank=True, null=True)
    """
    Any additional data about the change that does not fit in the columns
    above.
    """
