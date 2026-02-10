# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .batch import Batch
from .storage_location import StorageLocation


class Container(DatabaseTable):

    class Meta:
        db_table = "inventory_management__containers"

    # -------------------------------------------------------------------------

    html_display_name = "Containers"
    html_description_short = (
        "Containers are specific vessels that contain part (or all) of a batch. A "
        "single batch can have multiple containers because batches might need to be "
        "split up and/or have different storage destinations."
    )

    html_entries_template = "inventory_management/container/table.html"
    html_entry_template = "inventory_management/container/view.html"

    html_form_component = "container-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

    # -------------------------------------------------------------------------

    batch = table_column.ForeignKey(
        Batch,
        on_delete=table_column.CASCADE,
        blank=True,
        null=True,
        related_name="containers",
    )

    barcode = table_column.CharField(max_length=100, blank=True, null=True)

    location = table_column.ForeignKey(
        StorageLocation,
        on_delete=table_column.SET_NULL,
        blank=True,
        null=True,
        related_name="containers",
    )

    comments = table_column.TextField(
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    initial_amount = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )

    current_amount = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )

    amount_units_options = [
        "mg",
        "g",
        "kg",
        "ml",
        "l",
        "mol",
    ]
    amount_units = table_column.CharField(
        max_length=5,
        blank=True,
        null=True,
    )

    is_depleted = table_column.BooleanField(blank=True, null=True)

    # -------------------------------------------------------------------------
