from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef
from simple_history.models import HistoricalRecords

from simmate.database.core import table_column
from simmate.database.mixins import StatusTracking

from .batch import Batch
from .mixture import Mixture
from .substance import Substance


class InventoryRequest(StatusTracking):
    """
    A request for a new batch of a substance or mixture, such as:
        - a compound that a chemist or project wants made next (a "target")
        - more of a substance or mixture that was made in-house before (a
          "remake")
        - a substance or mixture to buy from a supplier or have custom-made by
          a contract lab (an "order")

    These all share one table. Whether a request is new or a remake is worked
    out from whether the substance or mixture had batches before the request
    was made (see `get_web_queryset`), and how it is sourced is given by
    `fulfillment_type`. Each request ends with the `batch` that fulfilled it.
    Requests are identified by their `display_id` (e.g. "REQ-123").
    """

    class Meta:
        db_table = "inventory_management__inventory_requests"
        verbose_name = "Inventory Request"

    id_prefix = "REQ"
    """
    The static prefix of every request's `display_id` (e.g. "REQ-123").
    """

    history = HistoricalRecords(
        table_name="inventory_management__inventory_requests__history"
    )
    """
    Every past version of each request, which gives the timestamp of each
    status change (see `StatusTracking`).
    """

    # -------------------------------------------------------------------------

    is_mixture = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether this request is for a `mixture` (True) or a single `substance`
    (False). Only the matching one of these two columns should be set.
    """

    substance = table_column.ForeignKey(
        Substance,
        on_delete=table_column.PROTECT,
        related_name="inventory_requests",
        blank=True,
        null=True,
    )
    """
    The substance that is requested. Only set when `is_mixture=False`.
    """

    mixture = table_column.ForeignKey(
        Mixture,
        on_delete=table_column.PROTECT,
        related_name="inventory_requests",
        blank=True,
        null=True,
    )
    """
    The mixture that is requested. Only set when `is_mixture=True`.
    """

    # -------------------------------------------------------------------------

    fulfillment_type_options = [
        "Internal Synthesis",
        "External Synthesis",
        "Purchased",
    ]
    fulfillment_type = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    """
    How the material will be sourced. Must be one of `fulfillment_type_options`,
    and is left empty until this is decided.

    These match the names in `Batch.batch_type_options`, so the batch that
    fulfills the request has the same type:
        - `Internal Synthesis`: made in-house
        - `External Synthesis`: custom-made by a contract lab or CRO
        - `Purchased`: bought from a supplier's catalog

    Together with the `status`, this gives the stage of a request (e.g. a
    "Purchased" request that is "In Progress" has been ordered).
    """

    # -------------------------------------------------------------------------

    amount = table_column.DecimalField(
        max_digits=16,
        decimal_places=3,
        blank=True,
        null=True,
    )
    """
    The amount of inventory requested, in `amount_units`.
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
    The units for `amount`. Must be one of `amount_units_options`.
    """

    needed_by = table_column.DateField(blank=True, null=True)
    """
    The date that the material is needed by.
    """

    priority_options = [
        "Low",
        "Medium",
        "High",
    ]
    priority = table_column.CharField(
        max_length=10,
        blank=True,
        null=True,
    )
    """
    How urgent the request is. Must be one of `priority_options`.
    """

    comments = table_column.TextField(blank=True, null=True)
    """
    Why the material is wanted (e.g. the design rationale of a target or what
    a remake will be used for), along with any other notes.
    """

    # -------------------------------------------------------------------------

    submitted_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="submitted_inventory_requests",
        blank=True,
        null=True,
    )
    """
    The user that entered this request into simmate, which is set automatically
    when the request is made. This differs from `requested_by` when someone
    submits a request on behalf of another person.
    """

    requested_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="requested_inventory_requests",
        blank=True,
        null=True,
    )
    """
    The user that wants the material (e.g. the chemist or project lead that
    asked for it).
    """

    assigned_to = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="assigned_inventory_requests",
        blank=True,
        null=True,
    )
    """
    The user that is working on the request (e.g. the chemist making it or the
    person placing the order).
    """

    completed_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="completed_inventory_requests",
        blank=True,
        null=True,
    )
    """
    The user that fulfilled the request. This is meant to be set automatically
    from the `batch` that fulfills it, once that batch is registered.
    """
    # TODO: set this automatically when a matching batch is registered

    project = table_column.ForeignKey(
        "project_management.Project",
        on_delete=table_column.SET_NULL,
        related_name="inventory_requests",
        blank=True,
        null=True,
    )
    """
    The project that the material is for, if any.
    """

    # -------------------------------------------------------------------------

    # Only for "External Synthesis" and "Purchased" requests. These match the
    # columns of `Batch`, so they can be copied over once the material arrives.

    supplier = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The external vendor or contract lab that the material is sourced from
    (e.g. "Sigma-Aldrich").
    """

    supplier_catalog_number = table_column.CharField(
        max_length=100, blank=True, null=True
    )
    """
    The `supplier`'s catalog/product number for the material.
    """

    estimated_cost = table_column.FloatField(blank=True, null=True)
    """
    The expected cost of the material from the `supplier`, in USD.
    """

    # -------------------------------------------------------------------------

    batch = table_column.ForeignKey(
        Batch,
        on_delete=table_column.SET_NULL,
        related_name="inventory_requests",
        blank=True,
        null=True,
    )
    """
    The batch that fulfilled this request, which is set once it is "Completed".
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        # `was_made_before` marks remakes: the substance or mixture already had
        # a batch when the request was made. Batches made after the request
        # (e.g. the one that fulfilled it) don't count.
        earlier_batches = Batch.objects.filter(created_at__lt=OuterRef("created_at"))
        return cls.objects.select_related(
            "substance",
            "mixture",
            "project",
            "submitted_by",
            "requested_by",
            "assigned_to",
            "completed_by",
            "batch",
        ).annotate(
            was_made_before=(
                Exists(earlier_batches.filter(substance_id=OuterRef("substance_id")))
                | Exists(earlier_batches.filter(mixture_id=OuterRef("mixture_id")))
            )
        )
