from decimal import Decimal, InvalidOperation

from django.db import transaction

from simmate.website.data_explorer.components import TableComponent

from ..models import Batch, Container, UsageLog


class UsageLogComponent(TableComponent):
    table = UsageLog

    display_name = "Containers Usage Logs"
    description_short = (
        "Instances where a user interacts with a container, such as removing "
        "some material for an experiment."
    )

    template_names = {
        "entries": "inventory_management/usage_log/table.html",
        "entry": "inventory_management/usage_log/view.html",
        "search": "inventory_management/usage_log/form.html",
        "create": "inventory_management/usage_log/form.html",
        "update": "inventory_management/usage_log/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "id"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "source_container_id",
        "amount_removed",
    ]

    source_container: Container = None
    """
    The container that material is being removed from, as found with the
    `container_lookup` input. It is summarized in the form so the user can
    confirm it is the right one.
    """

    post_data_mappings = {
        # barcodes can be all digits (e.g. "00123"), so this stays a str
        "container_lookup": str,
    }

    def mount_for_create(self):
        # Auto-fill user if we have access to request
        if hasattr(self, "request") and self.request and self.request.user:
            self.update_form("user_id", self.request.user.id)

    def mount_extra(self):
        # The container can be given in the URL (e.g. by the "Log Usage"
        # button of a container's page), which is only parsed after
        # `mount_for_create`
        container_id = self.form_data.get("source_container_id")
        if self.component_type == "create" and container_id:
            self.update_form("container_lookup", str(container_id))

    def pre_parse(self):
        # Unchecked checkboxes aren't posted at all, so this is reset on every
        # request (and set again if it is still checked)
        self.form_data.pop("mark_depleted", None)

    def on_change_hook__container_lookup(self):
        try:
            self.source_container = Container.get_by_barcode_or_id(
                self.form_data["container_lookup"]
            )
            self.form_data["source_container_id"] = self.source_container.id
        except Container.DoesNotExist:
            self.source_container = None
            self.form_data["source_container_id"] = None

    def check_form_for_create(self):
        self.check_required_inputs()

        # negative numbers are posted as str, so this is parsed here
        amount_removed = self.form_data.get("amount_removed")
        try:
            is_positive = Decimal(str(amount_removed)) > 0
        except InvalidOperation:
            is_positive = False
        if amount_removed is not None and not is_positive:
            self.form_errors.append("'amount_removed' must be greater than 0.")

        destination_batch_id = self.form_data.get("destination_batch_id")
        if (
            destination_batch_id
            and not Batch.objects.filter(id=destination_batch_id).exists()
        ):
            self.form_errors.append(
                "'destination_batch_id' must be the ID of an existing batch."
            )

    def save_to_db_for_create(self):
        with transaction.atomic():
            super().save_to_db_for_create()
            self.table_entry.deduct_from_container(
                mark_depleted=bool(self.form_data.get("mark_depleted"))
            )

    # -------------------------------------------------------------------------

    # UPDATE

    def save_to_db_for_update(self):
        # The default repeats `save_to_db_for_create`, which would remove the
        # amount from the container a second time. Updates only save the log.
        super().save_to_db_for_create()

    mount_for_update_columns = [
        "source_container_id",
        "destination_batch_id",
        "user_id",
        "amount_removed",
        "comments",
    ]
