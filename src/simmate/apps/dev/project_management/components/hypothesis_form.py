# -*- coding: utf-8 -*-

from django.db import transaction

from simmate.website.core_components.components import DynamicFormComponent, UserInput

from ..models import Hypothesis
from .mixins import ProjectManagementInput


class HypothesisFormView(DynamicFormComponent, UserInput, ProjectManagementInput):

    # Note: ProjectManagementInput has options for Hypotheses, but we don't use any
    # of those features.

    template_name = "projects/hypothesis/form.html"
    table = Hypothesis

    required_inputs = [
        "project_id",
        "created_by_id",
        "driven_by_id",
        "status",
        "name",
        "description",
        "comments",
    ]
    search_inputs = [
        "project_id",
        "created_by_id",
        "driven_by_id",
        "status",
        "name",
    ]

    # -------------------------------------------------------------------------

    driven_by_id = None
    created_by_id = None

    status = None
    status_options = Hypothesis.status_choices

    name = None
    description = None
    comments = None

    tag_name = None
    description = None

    # -------------------------------------------------------------------------

    class Meta:
        javascript_exclude = (
            "status_options",
            "tag_options",
            *UserInput.Meta.javascript_exclude,
            *DynamicFormComponent.Meta.javascript_exclude,
            *ProjectManagementInput.Meta.javascript_exclude,
        )

    def mount_for_update(self):
        super().mount_for_update()
        self.tag_ids = list(self.table_entry.tags.values_list("id", flat=True).all())

    def mount_extra(self):
        if self.form_mode == "create":
            if not self.driven_by_id:
                self.driven_by_id = self.request.user.id
            if not self.created_by_id:
                self.created_by_id = self.request.user.id

    def save_to_db(self):

        if self.form_mode not in ["create", "update"]:
            return  # nothing to save

        with transaction.atomic():
            self.table_entry.save()
            if self.tag_ids:
                self.table_entry.tags.set(self.tag_ids)
                self.table_entry.save()
