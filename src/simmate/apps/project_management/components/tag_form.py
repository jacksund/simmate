# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Project, Tag


class TagForm(DynamicTableForm):

    table = Tag

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
