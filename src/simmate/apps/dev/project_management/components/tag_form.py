# -*- coding: utf-8 -*-


from simmate.website.core_components.components import DynamicFormComponent

from ..models import Project, Tag


class TagFormView(DynamicFormComponent):

    template_name = "projects/tag/form.html"
    table = Tag

    # -------------------------------------------------------------------------

    required_inputs = [
        "tag_type",
        "name",
        "description",
    ]
    search_inputs = [
        "name",
        "tag_type",
        "project_id",
    ]

    class Meta:
        javascript_exclude = (
            "tag_type_options",
            "project_options",
            *DynamicFormComponent.Meta.javascript_exclude,
        )

    def mount_extra(self):
        self.project_options = Project.project_options

    # -------------------------------------------------------------------------

    tag_type = None
    tag_type_options = [(o, o) for o in Tag.tag_type_options]

    project_id = None
    project_options = []  # set by mount()

    name = None

    description = None

    def set_tag_type(self, tag_type):
        self.tag_type = tag_type
        if self.tag_type == "project-specific":
            self.call("refresh_select2")
