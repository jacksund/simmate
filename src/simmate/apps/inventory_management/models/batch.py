from django.contrib.auth.models import User
from django.db.models import Case, Count, Exists, OuterRef, Subquery, Sum, When
from django.db.models.functions import Coalesce

from simmate.database.core import DatabaseTable, table_column
from simmate.utils import chunk_list

from .mixture import Mixture
from .substance import Substance


class Batch(DatabaseTable):
    """
    A specific instance of a substance or mixture. For example, the product of
    a single synthesis or the delivery of a purchased chemical would each be
    one batch.

    A batch can be split across one or more containers (see `Container`), and
    batches can be linked to one another to track their lineage (see
    `parent_batches`). Batches are identified by their `display_id` (e.g.
    "B-123").
    """

    class Meta:
        db_table = "inventory_management__batches"

    id_prefix = "B"
    """
    The static prefix of every batch's `display_id` (e.g. "B-123").
    """

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

    batch_type_options = [
        "internal_synthesis",
        "external_synthesis",
        "purchased",
        "isolated",
        "prepared",
        "reprocessed",
        "aliquot",
        "pooled",
        "unknown",
        "other",
    ]
    batch_type = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    """
    How this batch was obtained. Must be one of `batch_type_options`.

    For example:
        - `internal_synthesis`: made in-house by a chemical reaction, including
          its workup and purification
        - `external_synthesis`: custom-made by a contract lab or CRO
        - `purchased`: bought from a supplier's catalog
        - `isolated`: separated out of a natural source or a parent mixture
          (e.g. an extract or a chromatography fraction). This is not the
          purification step of a normal synthesis, which is still an
          `internal_synthesis`.
        - `prepared`: made by combining or diluting other batches without a
          reaction (e.g. a stock solution or a formulation)
        - `reprocessed`: an existing batch that was repurified, recrystallized,
          dried, or milled
        - `aliquot`: split off from a parent batch. Only use this when the
          portion needs its own identity (e.g. separate QC or it is sent to
          another group). Otherwise, add a container to the existing batch.
        - `pooled`: several batches of the same substance or mixture combined
          into one
        - `unknown`: the origin is not known (e.g. legacy or bulk-imported
          records)

    For `prepared`, `reprocessed`, `aliquot`, and `pooled` batches, the source
    batches should be set in `parent_batches`.
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

    num_available_containers = table_column.IntegerField(blank=True, null=True)
    """
    The number of containers of this batch that are not empty (i.e. not
    depleted). See `update_cached_columns`.
    """

    total_initial_amount = table_column.DecimalField(
        max_digits=16,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The sum of `initial_amount` across all containers of this batch, in
    `amount_units`.
    """

    total_current_amount = table_column.DecimalField(
        max_digits=16,
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

    @classmethod
    def update_cached_columns(cls, batch_ids: list[int]):
        """
        Recalculates the columns that are cached from linked containers
        (`num_available_containers`, `total_initial_amount`,
        `total_current_amount`, and `is_depleted`) for the given batches. Use
        this after their containers are added, removed, used, or depleted
        (e.g. after bulk loads).

        A batch is only marked as depleted if it has containers and none of
        them are in stock. Batches without any containers are left as not
        depleted, as their material still needs to be put somewhere.
        """
        from .container import Container  # local import to avoid circular dep

        containers = Container.objects.filter(batch=OuterRef("pk")).order_by()
        in_stock = containers.exclude(is_depleted=True)
        # done in chunks to stay under the database's limit on query params
        for chunk in chunk_list(list(batch_ids), chunk_size=10_000):
            cls.objects.filter(id__in=chunk).update(
                num_available_containers=Coalesce(
                    Subquery(
                        in_stock.values("batch")
                        .annotate(count=Count("id"))
                        .values("count")
                    ),
                    0,
                ),
                total_initial_amount=Subquery(
                    containers.values("batch")
                    .annotate(total=Sum("initial_amount"))
                    .values("total")
                ),
                total_current_amount=Subquery(
                    containers.values("batch")
                    .annotate(total=Sum("current_amount"))
                    .values("total")
                ),
                is_depleted=Case(
                    When(Exists(containers) & ~Exists(in_stock), then=True),
                    default=False,
                ),
            )

    # -------------------------------------------------------------------------
