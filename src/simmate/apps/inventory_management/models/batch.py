# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .mixture import Mixture
from .substance import Substance


class Batch(DatabaseTable):

    class Meta:
        db_table = "inventory_management__batches"

    html_display_name = "Batches"
    html_description_short = (
        "Batches are specific instances of a substance or mixture. For example, "
        "the product of a single synthesis or the delievery a purchased chemical "
        "would each be one batch. One batch can then be stored in one or more containers."
    )

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    is_mixture = table_column.BooleanField(blank=True, null=True)

    substance = table_column.ForeignKey(
        Substance,
        on_delete=table_column.CASCADE,
        related_name="batches",
        blank=True,
        null=True,
    )

    mixture = table_column.ForeignKey(
        Mixture,
        on_delete=table_column.CASCADE,
        related_name="batches",
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    batch_number = table_column.IntegerField(blank=True, null=True)

    comments = table_column.TextField(
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    purity = table_column.FloatField(blank=True, null=True)

    expiration_date = table_column.DateTimeField(blank=True, null=True)

    # -------------------------------------------------------------------------

    supplier = table_column.CharField(max_length=100, blank=True, null=True)

    supplier_catalog_number = table_column.CharField(
        max_length=100, blank=True, null=True
    )

    # -------------------------------------------------------------------------

    # cached properties calculated from linked containers

    num_containers = table_column.IntegerField(blank=True, null=True)

    total_initial_amount = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )

    total_current_amount = table_column.DecimalField(
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
    # !!! what if containers use different units? this should be standardized

    is_depleted = table_column.BooleanField(blank=True, null=True)

    # -------------------------------------------------------------------------

    # TODO: parent_batches -- if we want to track lineage of batches
