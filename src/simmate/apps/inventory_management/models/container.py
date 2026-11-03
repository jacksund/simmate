from simmate.database.core import DatabaseTable, table_column

from .batch import Batch
from .storage_location import StorageLocation


class Container(DatabaseTable):
    """
    A physical vessel (vial, bottle, etc.) that holds part or all of a batch.

    A single batch can have multiple containers because batches might need to
    be split up and/or have different storage locations. Material removed from
    a container is recorded with a `UsageLog`. Containers are identified by
    their `display_id` (e.g. "C-123").
    """

    class Meta:
        db_table = "inventory_management__containers"

    id_prefix = "C"
    """
    The static prefix of every container's `display_id` (e.g. "C-123").
    """

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

    @classmethod
    def get_web_queryset(cls):
        # loads what the container table shows in one query (not one per row)
        return cls.objects.select_related(
            "batch__substance",
            "batch__mixture",
            "location",
        )

    @classmethod
    def get_by_barcode_or_id(cls, value: str | int) -> "Container":
        """
        Loads a container from a scanned barcode or a typed ID (along with its
        batch, substance or mixture, and location). Barcodes are checked
        first, as they are what scanners give and they can be all digits.
        Typed IDs can be given with or without the prefix (e.g. "C-123" or
        "123").

        Raises:
            Container.DoesNotExist: if no container matches.
        """
        value = str(value or "").strip()
        containers = cls.get_web_queryset()
        container = containers.filter(barcode=value).first() if value else None
        number = value.upper().removeprefix(f"{cls.id_prefix}-")
        if not container and number.isdigit():
            container = containers.filter(id=int(number)).first()
        if not container:
            raise cls.DoesNotExist(f"No container found with barcode or ID: '{value}'")
        return container

    # -------------------------------------------------------------------------
