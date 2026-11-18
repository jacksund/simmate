from simmate.website.data_explorer.components import TableComponent

from ..models import Candidate, Project
from ..models import ProjectComponent as ProjectComponentTable
from .mixins import LeaderboardInput, ProjectInput


class ProjectComponentComponent(TableComponent, ProjectInput, LeaderboardInput):
    # NOTE: the model is imported under another name because `ProjectComponent`
    # is also the name of the web component for the Project table

    table = ProjectComponentTable

    display_name = "Project Components"
    description_short = (
        "The things that each project needs (e.g. the battery of a phone), "
        "along with the leaderboard each one picks from and the candidate "
        "that was chosen."
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
        "entries": "project_management/project_component/table.html",
        "entry": "project_management/project_component/view.html",
        "search": "project_management/project_component/form.html",
        "create": "project_management/project_component/form.html",
        "update": "project_management/project_component/form.html",
    }

    # -------------------------------------------------------------------------

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, and admins or the project's leaders can
        # add & edit components. (For creating, the project is only known once
        # the form is filled, so it's checked on submit.)
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or component_type == "create":
            return True
        if component_type == "update":
            return table_entry.project.leaders.filter(pk=user.pk).exists()
        return False

    # -------------------------------------------------------------------------

    @property
    def chosen_candidate_id_options(self) -> list[tuple[int, str]]:
        # only the candidates of the selected leaderboard
        leaderboard_id = self.form_data.get("leaderboard_id")
        if not leaderboard_id:
            return []
        candidates = (
            Candidate.objects.filter(leaderboard_id=leaderboard_id)
            .select_related("substance", "mixture")
            .order_by("-rating")
        )
        return [
            (
                c.id,
                f"{c.display_id}: "
                + (
                    c.mixture.display_id
                    if c.is_mixture
                    else c.substance.common_name or c.substance_id
                ),
            )
            for c in candidates
        ]

    def refresh_options(self):
        # the candidate options depend on the selected leaderboard
        self.js_actions = [
            {"refresh_select2": []},
        ]

    # -------------------------------------------------------------------------

    # CREATE + UPDATE

    required_inputs = [
        "project_id",
        "name",
        "leaderboard_id",
    ]

    mount_for_update_columns = [
        "project_id",
        "name",
        "leaderboard_id",
        "chosen_candidate_id",
        "notes",
    ]

    def check_form_for_create(self):
        self.check_required_inputs()
        if self.form_errors:
            return

        user = self.request.user
        if (
            not user.is_staff
            and not Project.objects.filter(
                id=self.form_data["project_id"],
                leaders=user,
            ).exists()
        ):
            self.form_errors.append("Only the project's leaders can add components.")

        self.check_chosen_candidate()

    def check_form_for_update(self):
        self.check_required_inputs()
        self.check_chosen_candidate()

    def check_chosen_candidate(self):
        # the chosen candidate must come from the component's leaderboard
        chosen_id = self.form_data.get("chosen_candidate_id")
        if chosen_id and not Candidate.objects.filter(
            id=chosen_id,
            leaderboard_id=self.form_data.get("leaderboard_id"),
        ):
            self.form_errors.append(
                "The chosen candidate must be a candidate of the selected leaderboard."
            )
