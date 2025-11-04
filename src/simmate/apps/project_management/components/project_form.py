# -*- coding: utf-8 -*-

from django.db import transaction

from simmate.website.htmx.components import DynamicTableForm, UserInput

from ..models import Project


class ProjectForm(DynamicTableForm, UserInput):

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
        super().check_form_for_create()

        project_name = self.form_data.get("name", None)
        if project_name:
            # make sure the Project name is a new one
            project_exists = Project.objects.filter(name=project_name).exists()
            if project_exists:
                self.form_errors.append(
                    f"A project with the name '{project_name}' already exists."
                )

    def save_to_db_for_create(self):
        # We are saving multiple objects, so we want to make sure ALL work.
        # If not, we roll back everything
        with transaction.atomic():
            # Save the request to the database
            self.table_entry.save()
            # add leaders and members
            self.table_entry.leaders.set(self.form_data["leader_ids"])
            self.table_entry.members.set(self.form_data["member_ids"])

    # -------------------------------------------------------------------------

    # UPDATE

    def mount_for_update(self):
        super().mount_for_update()
        self.form_data["leader_ids"] = list(
            self.table_entry.leaders.values_list("id", flat=True).all()
        )
        self.form_data["member_ids"] = list(
            self.table_entry.members.values_list("id", flat=True).all()
        )

    def check_form_for_update(self):
        self.check_required_inputs()

        # if the sure the Project name was changed, make sure it is a new one
        project_name = self.form_data.get("name", None)
        if project_name:
            project_exists = (
                Project.objects.filter(name=project_name)
                .exclude(id=self.table_entry.id)
                .exists()
            )
            if project_exists:
                self.form_errors.append(
                    f"A project with the name '{project_name}' already exists."
                )

    # -------------------------------------------------------------------------

    # CREATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # UPDATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # SEARCH

    def to_search_dict(self, **kwargs):
        search_dict = self._get_default_search_dict(**kwargs)

        leader_ids = search_dict.pop("leader_ids", None)
        if leader_ids:
            search_dict["leaders__id__in"] = leader_ids

        member_ids = search_dict.pop("leader_ids", None)
        if member_ids:
            search_dict["members__id__in"] = member_ids

        return search_dict

    # -------------------------------------------------------------------------

    def suggest_new_name(self):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------
