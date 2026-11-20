from functools import cached_property

from django.db.models import Count

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import UserInput

from ..models import Leaderboard


class LeaderboardComponent(TableComponent, UserInput):
    table = Leaderboard

    display_name = "Leaderboards"
    description_short = (
        "Rankings of candidates for a specific use (e.g. Gaming Phone "
        "Batteries), judged against each leaderboard's objective. Leaderboards "
        "go from general to specific, and projects pick from them."
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
        "entries": "project_management/leaderboard/table.html",
        "entry": "project_management/leaderboard/view.html",
        "search": "project_management/leaderboard/form.html",
        "create": "project_management/leaderboard/form.html",
        "update": "project_management/leaderboard/form.html",
    }

    # -------------------------------------------------------------------------

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, and only admins can create & edit
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        return user.is_staff

    # -------------------------------------------------------------------------

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Leaderboard) -> dict:

        # this leaderboard's candidates, best first
        candidates__limit = 25
        candidates__count = table_entry.candidates.count()
        candidates = table_entry.candidates.select_related(
            "substance", "mixture"
        ).order_by("-rating", "id")[:candidates__limit]
        candidates__truncated = candidates__count > candidates__limit

        # the projects that pick from this leaderboard
        components = table_entry.project_components.select_related(
            "project", "chosen_candidate"
        ).order_by("project__name", "name")

        # Walk down through the child leaderboards one level at a time to build
        # the tree. Only the first `max_nodes` are put in the tree.
        max_depth = 10
        max_nodes = 100
        table_entry.tree_children = []
        nodes = {table_entry.id: table_entry}
        descendant_ids = []
        level = [table_entry.id]
        for _ in range(max_depth):
            children = (
                Leaderboard.objects.filter(parent_leaderboard_id__in=level)
                .exclude(id__in=list(nodes) + descendant_ids)  # guards cycles
                .only("name", "parent_leaderboard_id")
                .order_by("name", "id")
            )
            level = []
            for child in children:
                descendant_ids.append(child.id)
                level.append(child.id)
                # the parent may have been left out of the tree by the cap
                if len(nodes) <= max_nodes and child.parent_leaderboard_id in nodes:
                    child.tree_children = []
                    nodes[child.parent_leaderboard_id].tree_children.append(child)
                    nodes[child.id] = child
            if not level:
                break
        # count all child leaderboards, so that we can say how many are not shown
        counts = dict(
            Leaderboard.objects.filter(parent_leaderboard_id__in=list(nodes))
            .values_list("parent_leaderboard_id")
            .annotate(count=Count("id"))
            .order_by()
        )
        for node in nodes.values():
            node.tree_more = counts.get(node.id, 0) - len(node.tree_children)

        return {
            "leaderboard_path": table_entry.get_path(),
            "child_leaderboards__count": len(descendant_ids),
            "candidates": candidates,
            "candidates__count": candidates__count,
            "candidates__truncated": candidates__truncated,
            "components": components,
        }

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "name",
    ]

    @cached_property
    def parent_leaderboard_id_options(self) -> list[tuple[int, str]]:
        leaderboards = Leaderboard.objects.order_by("name").values_list("id", "name")
        table_entry = getattr(self, "table_entry", None)
        if table_entry:
            # a leaderboard can't be its own parent
            leaderboards = leaderboards.exclude(id=table_entry.id)
        return list(leaderboards)

    def mount_for_create(self):
        self.update_form("rating_system", "glicko")

    def check_form_for_create(self):
        super().check_form_for_create()
        self.check_name_is_new()

    def check_name_is_new(self):
        # Names only need to be unique next to their siblings, as the path
        # tells apart leaderboards elsewhere in the tree
        name = self.form_data.get("name", None)
        if not name:
            return
        siblings = Leaderboard.objects.filter(
            name=name,
            parent_leaderboard_id=self.form_data.get("parent_leaderboard_id") or None,
        )
        table_entry = getattr(self, "table_entry", None)
        if table_entry and table_entry.id:
            siblings = siblings.exclude(id=table_entry.id)
        if siblings.exists():
            self.form_errors.append(
                f"A leaderboard named '{name}' already exists under this parent."
            )

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "name",
        "description",
        "objective",
        "rating_system",
        "parent_leaderboard_id",
    ]

    def check_form_for_update(self):
        self.check_required_inputs()

        # the parent can't be this leaderboard or one nested inside of it, as
        # that would create a cycle
        parent_id = self.form_data.get("parent_leaderboard_id", None)
        if parent_id:
            nested_ids = {self.table_entry.id}
            level = [self.table_entry.id]
            while level and int(parent_id) not in nested_ids:
                level = list(
                    Leaderboard.objects.filter(parent_leaderboard_id__in=level)
                    .exclude(id__in=nested_ids)
                    .values_list("id", flat=True)
                )
                nested_ids.update(level)
            if int(parent_id) in nested_ids:
                self.form_errors.append(
                    "A leaderboard's parent can't be itself or one of its "
                    "child leaderboards."
                )

        self.check_name_is_new()

    # -------------------------------------------------------------------------

    def save_to_db_for_update(self):
        # ratings depend on the rating system, so they're rebuilt when it changes
        old_rating_system = Leaderboard.objects.values_list(
            "rating_system", flat=True
        ).get(id=self.table_entry.id)
        super().save_to_db_for_update()
        if self.table_entry.rating_system != old_rating_system:
            self.table_entry.recalculate_ratings()
