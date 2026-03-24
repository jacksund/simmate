# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Project, Tag


class TagForm(DynamicTableForm):

    table = Tag

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "project_management/tag/table.html",
        "entry": "project_management/tag/view.html",
    }

    display_name = "Tags, Labels, & Categories"
    description_short = (
        "Customizable labels that help with organizing project items like "
        "hypotheses, targets, and orders. Tags allow for flexible "
        "filtering and categorization."
    )

    enabled_forms = [
        "search",
        "create",
        "update",
    ]

    template_name = "project_management/tag/form.html"

    # -------------------------------------------------------------------------

    def mount_extra(self):
        self.project_options = Project.project_options

    def update_tag_type(self):
        if self.form_data.get("tag_type") == "project-specific":
            self.js_actions = [
                {"refresh_select2": []},
            ]

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "tag_type",
        "name",
        "description",
    ]

    # -------------------------------------------------------------------------
