from collections import defaultdict

from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Q
from simple_history.models import HistoricalRecords

from simmate.database.core import table_column
from simmate.database.mixins import StatusTracking
from simmate.toolkit import Molecule as ToolkitMolecule

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

    Requests made together (e.g. 40 targets for one project) can be grouped
    into an `InventoryRequestList` (see `request_list`).
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

    # the same as batches, so that the fulfilling batch can use these units
    amount_units_options = Batch.amount_units_options
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

    request_list = table_column.ForeignKey(
        "InventoryRequestList",
        on_delete=table_column.SET_NULL,
        related_name="requests",
        blank=True,
        null=True,
    )
    """
    The list that this request was submitted with, if any (e.g. "RL-12").
    Single requests (e.g. from a substance's "Request More" button) don't need
    one. Values shared by a list's requests (e.g. `project`) were copied onto
    each request when the list was made, so each request can still be edited
    on its own.
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
            "request_list",
        ).annotate(
            was_made_before=(
                Exists(earlier_batches.filter(substance_id=OuterRef("substance_id")))
                | Exists(earlier_batches.filter(mixture_id=OuterRef("mixture_id")))
            )
        )

    # -------------------------------------------------------------------------

    @classmethod
    def resolve_items(cls, items: list[str]) -> dict[str, dict]:
        """
        Works out what each requested item is, where an item is the text that
        a user typed or uploaded for it: a substance ID (e.g. "BCD-012-3456"),
        a mixture ID (e.g. "BCDF-123"), or a SMILES.

        All items are checked together with a fixed number of queries. This
        only reads the database (e.g. datastore-only substances are not copied
        and SMILES are not registered), so it is safe to use for previews.

        Args:
            items: The items to look up. Blank items are skipped.

        Returns:
            A dictionary that maps each item (with whitespace stripped) to a
            dictionary of:
                - `kind`: "substance", "mixture", "smiles", or "invalid"
                - `substance_id`: the current ID of the substance (following
                  merges). For SMILES, this is a preview of the registered
                  substance with the same InChIKey, which is None if the
                  SMILES is new.
                - `mixture_id`: the integer ID of the mixture
                - `inchi_key`: only set for SMILES
                - `merged_from`: the given substance ID if it was merged into
                  or promoted to another (else None)
                - `open_request_ids`: the display IDs of open requests for
                  the same substance or mixture
                - `error`: why the item is invalid (else None)
        """
        infos = {}
        substance_items = {}  # item --> substance ID (uppercase)
        mixture_items = {}  # item --> mixture display ID (uppercase)
        for item in {item.strip() for item in items if item and item.strip()}:
            info = dict(
                kind="invalid",
                substance_id=None,
                mixture_id=None,
                inchi_key=None,
                merged_from=None,
                open_request_ids=[],
                error=None,
            )
            infos[item] = info
            upper = item.upper()
            if Substance.validate_id(upper):
                info["kind"] = "substance"
                substance_items[item] = upper
            elif Mixture.validate_display_id(upper):
                info["kind"] = "mixture"
                mixture_items[item] = upper
            else:
                try:
                    info["inchi_key"] = ToolkitMolecule.from_smiles(item).to_inchi_key()
                except Exception:
                    pass
                if info["inchi_key"]:
                    info["kind"] = "smiles"
                else:
                    info["error"] = "is not a substance ID, mixture ID, or SMILES"

        # Substances, following any merges or promotions
        current_ids = Substance.resolve_ids(list(set(substance_items.values())))
        delisted = set(
            Substance.objects.filter(
                id__in={i for i in current_ids.values() if i},
                is_delisted=True,
            ).values_list("id", flat=True)
        )
        for item, substance_id in substance_items.items():
            info = infos[item]
            current_id = current_ids[substance_id]
            if not current_id:
                info["kind"] = "invalid"
                info["error"] = "is not a registered substance ID"
            elif current_id in delisted:
                info["kind"] = "invalid"
                info["error"] = "is a delisted substance ID"
            else:
                info["substance_id"] = current_id
                if current_id != substance_id:
                    info["merged_from"] = substance_id

        # Mixtures
        mixtures = Mixture.get_by_display_ids(list(set(mixture_items.values())))
        for item, display_id in mixture_items.items():
            info = infos[item]
            mixture = mixtures.get(display_id)
            if not mixture:
                info["kind"] = "invalid"
                info["error"] = "is not a registered mixture ID"
            else:
                info["mixture_id"] = mixture.id

        # SMILES. This only previews whether each is already registered (as
        # a molecule-only substance), as the final match is made by
        # `SubstanceDatastore.get_or_create_ids` when the request is saved.
        smiles_infos = [info for info in infos.values() if info["kind"] == "smiles"]
        if smiles_infos:
            inchi_keys = {info["inchi_key"] for info in smiles_infos}
            # ordered newest first, so that the oldest match is kept
            matches = dict(
                Substance.objects.filter(
                    molecule__inchi_key__in=inchi_keys,
                    structure__isnull=True,
                )
                .exclude(is_delisted=True)
                .order_by("-created_at")
                .values_list("molecule__inchi_key", "id")
            )
            for info in smiles_infos:
                info["substance_id"] = matches.get(info["inchi_key"])

        # Open requests for the same substances and mixtures
        substance_ids = {i["substance_id"] for i in infos.values()} - {None}
        mixture_ids = {i["mixture_id"] for i in infos.values()} - {None}
        if substance_ids or mixture_ids:
            open_requests = defaultdict(list)  # (substance, mixture) --> REQ ids
            for request_id, substance_id, mixture_id in (
                cls.objects.filter(status__in=cls.open_status_options)
                .filter(
                    Q(substance_id__in=substance_ids) | Q(mixture_id__in=mixture_ids)
                )
                .order_by("id")
                .values_list("id", "substance_id", "mixture_id")
            ):
                open_requests[(substance_id, mixture_id)].append(
                    f"{cls.id_prefix}-{request_id}"
                )
            for info in infos.values():
                info["open_request_ids"] = open_requests.get(
                    (info["substance_id"], info["mixture_id"]), []
                )

        return infos
