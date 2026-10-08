# -*- coding: utf-8 -*-

from simmate.database.core import DatabaseTable, table_column

from .batch import Batch
from .storage_location import StorageLocation


class Container(DatabaseTable):
    """
    A physical vessel (vial, bottle, etc.) that holds part or all of a batch.

    A single batch can have multiple containers because batches might need to
    be split up and/or have different storage locations. Material removed from
    a container is recorded with a `UsageLog`.
    """

    class Meta:
        db_table = "inventory_management__containers"

    # -------------------------------------------------------------------------

    batch = table_column.ForeignKey(
        Batch,
        on_delete=table_column.CASCADE,
        blank=True,
        null=True,
        related_name="containers",
    )
    """
    The batch that the contents of this container belong to.
    """

    container_type_options = [
        "vial",
        "test tube",
        "bottle",
        "jar",
        "flask",
        "ampoule",
        "centrifuge tube",
        "microcentrifuge tube",
        "storage tube",
        "well plate",
        "well",
        "syringe",
        "bag",
        "can",
        "drum",
        "barrel",
        "gas cylinder",
        "other",
    ]
    container_type = table_column.CharField(
        max_length=30,
        blank=True,
        null=True,
    )
    """
    The kind of vessel this is. Must be one of `container_type_options`.
    """

    barcode = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The barcode on the container's label, if any (e.g. as read by a scanner).
    """

    location = table_column.ForeignKey(
        StorageLocation,
        on_delete=table_column.SET_NULL,
        blank=True,
        null=True,
        related_name="containers",
    )
    """
    Where the container is currently stored.
    """

    comments = table_column.TextField(
        blank=True,
        null=True,
    )
    """
    Any extra notes about the container.
    """

    image = table_column.ImageField(
        upload_to="inventory_management/containers/",
        blank=True,
        null=True,
    )
    """
    A user-uploaded photo of the container
    """

    # -------------------------------------------------------------------------

    initial_amount = table_column.DecimalField(
        max_digits=16,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The amount of material in the container when it was first filled, in
    `amount_units`.
    """

    current_amount = table_column.DecimalField(
        max_digits=16,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The amount of material remaining in the container, in `amount_units`.
    This starts equal to `initial_amount` and decreases as material is
    removed (see `UsageLog`).
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
    The units for `initial_amount`, `current_amount`, and the `amount_removed`
    of any linked usage logs. Must be one of `amount_units_options`.
    """

    is_depleted = table_column.BooleanField(blank=True, null=True)
    """
    Whether the container is empty (or has too little left to be useful).
    """

    # -------------------------------------------------------------------------
