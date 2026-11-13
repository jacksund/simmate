from functools import cached_property

from django.db.models import Count

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

from ..models import Project
from .dashboard import STATUS_THEMES


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
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, admins can create, and admins or the
        # project's leaders can edit it
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if component_type == "update":
            return table_entry.leaders.filter(pk=user.pk).exists()
        return False

    # -------------------------------------------------------------------------

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Project) -> dict:

        count_limit = 50_000

        tags__limit = 10
        tags__count = table_entry.tags.all()[:count_limit].count()
        tags = table_entry.tags.order_by("-id").all()[:tags__limit]
        tags__truncated = bool(len(tags) >= tags__limit)

        # the leaderboard of this project's candidates
        candidates__limit = 25
        candidates__count = table_entry.candidates.count()
        candidates = table_entry.candidates.select_related(
            "substance", "mixture"
        ).order_by("-rating", "id")[:candidates__limit]
        candidates__truncated = candidates__count > candidates__limit

        # Walk down through the sub-projects one level at a time to build the
        # tree of sub-projects. Only the first `max_nodes` are put in the tree.
        max_depth = 10
        max_nodes = 100
        table_entry.tree_children = []
        nodes = {table_entry.id: table_entry}
        descendant_ids = []
        level = [table_entry.id]
        for _ in range(max_depth):
            children = (
                Project.objects.filter(parent_project_id__in=level)
                .exclude(id__in=list(nodes) + descendant_ids)  # guards cycles
                .only("name", "status", "discipline", "parent_project_id")
                .order_by("name", "id")
            )
            level = []
            for child in children:
                descendant_ids.append(child.id)
                level.append(child.id)
                # the parent may have been left out of the tree by the cap
                if len(nodes) <= max_nodes and child.parent_project_id in nodes:
                    child.tree_children = []
                    child.status_theme = STATUS_THEMES.get(child.status, "secondary")
                    nodes[child.parent_project_id].tree_children.append(child)
                    nodes[child.id] = child
            if not level:
                break
        # count all sub-projects, so that we can say how many are not shown
        counts = dict(
            Project.objects.filter(parent_project_id__in=list(nodes))
            .values_list("parent_project_id")
            .annotate(count=Count("id"))
            .order_by()
        )
        for node in nodes.values():
            node.tree_more = counts.get(node.id, 0) - len(node.tree_children)
        table_entry.status_theme = STATUS_THEMES.get(table_entry.status, "secondary")

        return {
            "project_path": table_entry.get_path(),
            "sub_projects__count": len(descendant_ids),
            "tags": tags,
            "tags__count": tags__count,
            "tags__truncated": tags__truncated,
            "candidates": candidates,
            "candidates__count": candidates__count,
            "candidates__truncated": candidates__truncated,
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

    @cached_property
    def parent_project_id_options(self) -> list[tuple[int, str]]:
        projects = Project.objects.order_by("name").values_list("id", "name")
        table_entry = getattr(self, "table_entry", None)
        if table_entry:
            # a project can't be its own parent
            projects = projects.exclude(id=table_entry.id)
        return list(projects)

    def mount_for_create(self):
        self.update_form("rating_system", "glicko")

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
        "parent_project_id",
        "objective",
        "rating_system",
    ]

    def check_form_for_update(self):
        self.check_required_inputs()

        # the parent can't be this project or one nested inside of it, as
        # that would create a cycle
        parent_id = self.form_data.get("parent_project_id", None)
        if parent_id:
            nested_ids = {self.table_entry.id}
            level = [self.table_entry.id]
            while level and int(parent_id) not in nested_ids:
                level = list(
                    Project.objects.filter(parent_project_id__in=level)
                    .exclude(id__in=nested_ids)
                    .values_list("id", flat=True)
                )
                nested_ids.update(level)
            if int(parent_id) in nested_ids:
                self.form_errors.append(
                    "A project's parent can't be itself or one of its sub-projects."
                )

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

    def save_to_db_for_update(self):
        # ratings depend on the rating system, so they're rebuilt when it changes
        old_rating_system = Project.objects.values_list("rating_system", flat=True).get(
            id=self.table_entry.id
        )
        super().save_to_db_for_update()
        if self.table_entry.rating_system != old_rating_system:
            self.table_entry.recalculate_ratings()

    # -------------------------------------------------------------------------

    def suggest_new_name(self):
        self.form_data["name"] = Project.suggest_new_name()

    # -------------------------------------------------------------------------
