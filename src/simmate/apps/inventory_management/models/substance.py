# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class Substance(DatabaseTable):

    class Meta:
        db_table = "inventory_management__substances"

    html_display_name = "Chemical Substances"
    html_description_short = (
        "A substance is any chemical entity, such as a specific molecule or material. "
        "Substances typically have a CAS number assigned that never changes, and "
        "many batches+containers can exist for a given substance."
    )

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    common_name = table_column.CharField(max_length=255, blank=True, null=True)

    cas_number = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    iupac_name = table_column.TextField(blank=True, null=True)

    description = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    substance_type_options = [
        "molecule",
        "material",
        "mixture",  # steel, brass, gasoline, seawater -- common mixes w. CAS
        "other",
    ]
    substance_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
