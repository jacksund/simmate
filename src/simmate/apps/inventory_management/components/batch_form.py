# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Batch


class BatchForm(DynamicTableForm):

    table = Batch

    template_name = "inventory_management/batch/form.html"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "is_mixture",
        # "substance_id", # only if is_mixture=False
        # "mixture_id",  # only if is_mixture=True
        # "batch_number",  # auto generated after creation (to avoid race condition)
    ]

    def mount_for_create(self):
        self.update_form("amount_units", "mg")
        self.update_form("is_depleted", False)

    def check_form_for_create(self):
        self.check_required_inputs()

        is_mixture = self.form_data["is_mixture"]
        if is_mixture and not self.form_data.get("mixture_id", None):
            self.form_errors.append(
                "'mixture_id' is a required input when `is_mixture=True"
            )
        if not is_mixture and not self.form_data.get("substance_id", None):
            self.form_errors.append(
                "'substance_id' is a required input when `is_mixture=False"
            )

    # -------------------------------------------------------------------------

    # UPDATE

    # -------------------------------------------------------------------------

    # CREATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # UPDATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # SEARCH

    # -------------------------------------------------------------------------
