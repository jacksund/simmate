# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column

from .mixture import Mixture
from .substance import Substance


class Batch(DatabaseTable):
    """
    A specific instance of a substance or mixture. For example, the product of
    a single synthesis or the delivery of a purchased chemical would each be
    one batch.

    A batch can be split across one or more containers (see `Container`), and
    batches can be linked to one another to track their lineage (see
    `parent_batches`).
    """

    class Meta:
        db_table = "inventory_management__batches"

    # -------------------------------------------------------------------------

    is_mixture = table_column.BooleanField(blank=True, null=True)
    """
    Whether this batch is of a `mixture` (True) or a single `substance` (False).
    Only the matching one of these two columns should be set.
    """

    substance = table_column.ForeignKey(
        Substance,
        on_delete=table_column.CASCADE,
        related_name="batches",
        blank=True,
        null=True,
    )
    """
    The substance that this batch is of. Only set when `is_mixture=False`.
    """

    mixture = table_column.ForeignKey(
        Mixture,
        on_delete=table_column.CASCADE,
        related_name="batches",
        blank=True,
        null=True,
    )
    """
    The mixture that this batch is of. Only set when `is_mixture=True`.
    """

    # -------------------------------------------------------------------------

    batch_number = table_column.IntegerField(blank=True, null=True)
    """
    A sequential number that counts the batches of a given substance or mixture
    (e.g. the 3rd batch ever made of a substance is batch number 3). This is
    assigned after the batch is created to avoid race conditions.
    """

    comments = table_column.TextField(
        blank=True,
        null=True,
    )
    """
    Any extra notes about the batch.
    """

    appearance = table_column.TextField(blank=True, null=True)
    """
    A description of how the batch looks (e.g. "white crystalline powder")
    """

    image = table_column.ImageField(
        upload_to="inventory_management/batches/",
        blank=True,
        null=True,
    )
    """
    A user-uploaded photo of the batch
    """

    # TODO: link to a lab notebook entry (e.g. ELN page/experiment) once a
    # Notebook model exists

    # -------------------------------------------------------------------------

    purity = table_column.FloatField(blank=True, null=True)
    """
    The purity of the batch as a percent (0-100).
    """

    expiration_date = table_column.DateTimeField(blank=True, null=True)
    """
    The date after which the batch should no longer be used.
    """

    # -------------------------------------------------------------------------

    supplier = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The external vendor that this batch was purchased from (e.g. "Sigma-Aldrich").
    Leave empty for batches made in-house.
    """

    supplier_catalog_number = table_column.CharField(
        max_length=100, blank=True, null=True
    )
    """
    The `supplier`'s catalog/product number for this batch.
    """

    supplied_by = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        related_name="supplied_batches",
        blank=True,
        null=True,
    )
    """
    The user that made or provided this batch (e.g. the chemist that ran the
    synthesis). Not to be confused with `supplier`, which is the external
    vendor of a purchased chemical.
    """

    # -------------------------------------------------------------------------

    # cached properties calculated from linked containers

    num_containers = table_column.IntegerField(blank=True, null=True)
    """
    The number of containers that this batch is stored in.
    """

    total_initial_amount = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The sum of `initial_amount` across all containers of this batch, in
    `amount_units`.
    """

    total_current_amount = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The sum of `current_amount` across all containers of this batch (i.e. the
    total amount remaining), in `amount_units`.
    """

    amount_units_options = [
        "ug",
        "mg",
        "g",
        "kg",
        "ul",
        "ml",
        "l",
        "mol",
    ]
    amount_units = table_column.CharField(
        max_length=5,
        blank=True,
        null=True,
    )
    """
    The units for `total_initial_amount` and `total_current_amount`. Must be
    one of `amount_units_options`.
    """
    # !!! what if containers use different units? this should be standardized

    is_depleted = table_column.BooleanField(blank=True, null=True)
    """
    Whether all containers of this batch are depleted (i.e. none of the batch
    remains).
    """

    # -------------------------------------------------------------------------

    parent_batches = table_column.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="child_batches",
        db_table="inventory_management__batch_lineage",
    )
    """
    The batches used to make this batch (e.g. the starting materials of a
    synthesis). This allows the lineage of a batch to be tracked.
    """

    # -------------------------------------------------------------------------
