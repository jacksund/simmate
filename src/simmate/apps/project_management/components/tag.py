from simmate.website.data_explorer.components import TableComponent

from ..models import Tag
from .mixins import ProjectInput


class TagComponent(TableComponent, ProjectInput):
    table = Tag

    template_names = {
        "entries": "project_management/tag/table.html",
        "entry": "project_management/tag/view.html",
        "search": "project_management/tag/form.html",
        "create": "project_management/tag/form.html",
        "update": "project_management/tag/form.html",
    }

    display_name = "Tags, Labels, & Categories"
    description_short = (
        "Customizable labels that help with organizing project items like "
        "hypotheses, targets, and orders. Tags allow for flexible "
        "filtering and categorization."
    )

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, admins can create, and admins or the
        # leaders of a project-specific tag's project can edit it
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if component_type == "update" and table_entry.project_id:
            return table_entry.project.leaders.filter(pk=user.pk).exists()
        return False

    # -------------------------------------------------------------------------

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
