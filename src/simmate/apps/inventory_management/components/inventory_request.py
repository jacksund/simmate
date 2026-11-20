from functools import cached_property

from simmate.apps.project_management.components.mixins import ProjectInput
from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

from ..models import Batch, InventoryRequest, InventoryRequestList, Mixture, Substance


class InventoryRequestComponent(TableComponent, UserInput, ProjectInput):
    table = InventoryRequest

    display_name = "Inventory Requests"
    description_short = (
        "Requests for new batches of substances or mixtures, such as "
        "compounds to make next (targets), more of something made before "
        "(remakes), and items to buy or have custom-made (orders)."
    )

    template_names = {
        "entries": "inventory_management/inventory_request/table.html",
        "entry": "inventory_management/inventory_request/view.html",
        "search": "inventory_management/inventory_request/form.html",
        "create": "inventory_management/inventory_request/form.html",
        "update": "inventory_management/inventory_request/form.html",
        "update_many": "inventory_management/inventory_request/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
        "update_many",
    ]

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, any signed-in user can make a request, and
        # admins, the submitter, the requester, or the assigned user can edit it.
        # Only admins can update many requests at once ("update_many"), as the
        # selected requests aren't checked one by one.
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or component_type == "create":
            return True
        if component_type == "update":
            return user.id in [
                table_entry.submitted_by_id,
                table_entry.requested_by_id,
                table_entry.assigned_to_id,
            ]
        return False

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: InventoryRequest) -> dict:
        # the entry page loads the row without `get_web_queryset`, so it is
        # reloaded with its related rows and `was_made_before` (and replaces
        # the given entry)
        return {
            "table_entry": InventoryRequest.get_web_queryset().get(id=table_entry.id)
        }

    # -------------------------------------------------------------------------

    @cached_property
    def request_list_options(self) -> list[tuple[int, str]]:
        """
        The newest request lists (e.g. "RL-12: Round 3 targets"), plus the
        current list of the form if it is older.
        """
        lists = InventoryRequestList.objects.order_by("-id")
        current_id = self.form_data.get("request_list_id")
        options = list(lists.values_list("id", "title")[:50])
        if current_id and current_id not in [option[0] for option in options]:
            options += list(lists.filter(id=current_id).values_list("id", "title"))
        prefix = InventoryRequestList.id_prefix
        return [(id, f"{prefix}-{id}: {title or ''}") for id, title in options]

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "is_mixture",
        # "substance_id",  # only if is_mixture=False
        # "mixture_id",  # only if is_mixture=True
    ]

    def mount_for_create(self):
        self.update_form("is_mixture", False)
        self.update_form("status", "Under Review")
        # most people request material for themselves, but this can be changed
        # to submit a request on behalf of someone else
        self.update_form("requested_by_id", self.request.user.id)

    def mount_extra(self):
        # The item can be given in the URL (e.g. by the "Request More" button
        # of a substance or mixture page), which is only parsed after
        # `mount_for_create`
        if self.component_type == "create" and self.form_data.get("mixture_id"):
            self.update_form("is_mixture", True)

    def check_form_for_create(self):
        self.check_required_inputs()
        if self.form_errors:
            return

        # Substances and mixtures are typed in by their IDs, so these are
        # looked up and swapped for the real database IDs here
        if self.form_data["is_mixture"]:
            self.form_data["substance_id"] = None
            try:
                mixture = Mixture.get_by_display_id(
                    str(self.form_data.get("mixture_id") or "")
                )
            except Mixture.DoesNotExist:
                self.form_errors.append(
                    "'mixture_id' must be the ID of an existing mixture (e.g. BCDF-123)."
                )
                return
            self.form_data["mixture_id"] = mixture.id
        else:
            self.form_data["mixture_id"] = None
            try:
                # this follows merged IDs and loads datastore-only substances
                substance = Substance.get_by_id(
                    str(self.form_data.get("substance_id") or "")
                )
            except Substance.DoesNotExist:
                self.form_errors.append(
                    "'substance_id' must be the ID of an existing substance "
                    "(e.g. BCD-012-3456)."
                )
                return
            self.form_data["substance_id"] = substance.id

        self.check_request_list()

    def check_request_list(self):
        request_list_id = self.form_data.get("request_list_id")
        if (
            request_list_id
            and not InventoryRequestList.objects.filter(id=request_list_id).exists()
        ):
            self.form_errors.append(
                "'request_list_id' must be the ID of an existing request list."
            )

    def unmount_for_create(self):
        super().unmount_for_create()
        self.table_entry.submitted_by = self.request.user

    # -------------------------------------------------------------------------

    # UPDATE

    # the requested substance or mixture can't be swapped once made
    mount_for_update_columns = [
        "status",
        "fulfillment_type",
        "amount",
        "amount_units",
        "needed_by",
        "priority",
        "requested_by_id",
        "assigned_to_id",
        "project_id",
        "request_list_id",
        "supplier",
        "supplier_catalog_number",
        "estimated_cost",
        "batch_id",
        "comments",
    ]

    def check_form_for_update(self):
        # the fulfilling batch must be of the requested substance or mixture
        batch_id = self.form_data.get("batch_id")
        if (
            batch_id
            and not Batch.objects.filter(
                id=batch_id,
                substance_id=self.table_entry.substance_id,
                mixture_id=self.table_entry.mixture_id,
            ).exists()
        ):
            self.form_errors.append(
                "'batch_id' must be the ID of a batch of the requested substance "
                "or mixture."
            )
        self.check_request_list()

    # -------------------------------------------------------------------------

    # UPDATE MANY

    # e.g. approving or assigning every request of a list at once (from the
    # InventoryRequest table filtered by `request_list_id`)

    n_ids_to_update_max = InventoryRequestList.max_requests

    # the requested item and its fulfilling batch are set one request at a time
    ignore_on_update_many = [
        "is_mixture",
        "substance_id",
        "mixture_id",
        "batch_id",
    ]

    def check_form_for_update_many(self):
        super().check_form_for_update_many()
        self.check_request_list()
