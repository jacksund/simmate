# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, UserInput

from ..models import Project


class ProjectForm(DynamicTableForm, UserInput):

    table = Project

    template_name = "project_management/project/form.html"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "name",
        "description",
        "discipline",
        "status",
        "leaders__ids",
        "members__ids",
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

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "name",
        "description",
        "discipline",
        "status",
        "leaders__ids",
        "members__ids",
    ]

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

    # -------------------------------------------------------------------------

    def suggest_new_name(self):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------
