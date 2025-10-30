# -*- coding: utf-8 -*-

from django.db import transaction

from simmate.website.htmx.components import DynamicTableForm

from ..models import Project


class ProjectForm(DynamicTableForm):  # UserInput

    table = Project

    template_names = dict(
        default="project_management/project/form.html",
    )

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "name",
        "description",
        "discipline",
        "status",
        "leader_ids",
        "member_ids",
    ]

    def check_form_for_create(self):
        # make sure the Project name is a new one
        project_exists = Project.objects.filter(name=self.name).exists()
        if project_exists:
            self.form_errors.append(
                f"A project with the name {self.name} already exists."
            )

    # -------------------------------------------------------------------------

    # UPDATE

    def mount_for_update(self):
        super().mount_for_update()
        self.leader_ids = list(
            self.table_entry.leaders.values_list("id", flat=True).all()
        )
        self.member_ids = list(
            self.table_entry.members.values_list("id", flat=True).all()
        )

    def check_form_for_update(self):
        # if the sure the Project name was changed, make sure it is a new one
        project_exists = (
            Project.objects.filter(name=self.name)
            .exclude(id=self.table_entry.id)
            .exists()
        )
        if project_exists:
            self.form_errors.append(
                f"A project with the name {self.name} already exists."
            )

    # -------------------------------------------------------------------------

    # CREATE MANY

    # -------------------------------------------------------------------------

    # UPDATE MANY

    # -------------------------------------------------------------------------

    # SEARCH

    search_inputs = [
        "name",
        "status",
        "discipline",
    ]

    # -------------------------------------------------------------------------

    def save_to_db(self):

        if self.form_mode not in ["create", "update"]:
            return  # nothing to save

        # We are saving multiple objects, so we want to make sure ALL work.
        # If not, we roll back everything
        with transaction.atomic():
            # Save the request to the database
            self.table_entry.save()
            # add leaders and members
            self.table_entry.leaders.set(self.leader_ids)
            self.table_entry.members.set(self.member_ids)

    def to_search_dict(self, **kwargs):
        search = self._get_default_search_dict(**kwargs)
        if self.leader_ids:
            search["leaders__id__in"] = self.leader_ids
        if self.member_ids:
            search["members__id__in"] = self.member_ids
        return search

    # -------------------------------------------------------------------------

    def suggest_new_name(self, request):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------
