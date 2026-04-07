# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

from ..models import Project


class ProjectComponent(TableComponent, UserInput):

    table = Project

    display_name = "Projects"
    description_short = (
        "A container for a collection of related chemistry tasks, hypotheses, "
        "and results. Projects help group and manage scientific work into "
        "discrete units."
    )
    tabtitle_label_col = "name"

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    template_names = {
        "entries": "project_management/project/table.html",
        "entry": "project_management/project/view.html",
        "search": "project_management/project/form.html",
        "create": "project_management/project/form.html",
        "update": "project_management/project/form.html",
    }

    # -------------------------------------------------------------------------

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Project) -> dict:

        count_limit = 50_000

        tags__limit = 10
        tags__count = table_entry.tags.all()[:count_limit].count()
        tags = table_entry.tags.order_by("-id").all()[:tags__limit]
        tags__truncated = bool(len(tags) >= tags__limit)

        return {
            "tags": tags,
            "tags__count": tags__count,
            "tags__truncated": tags__truncated,
        }

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

    def suggest_new_name(self):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------


# DEPRECATED: use ProjectComponent instead
ProjectForm = ProjectComponent
