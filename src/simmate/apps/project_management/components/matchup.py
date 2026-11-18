from django.db.models import Q
from django.shortcuts import redirect

from simmate.website.data_explorer.components import TableComponent

from ..models import Candidate, Matchup, Project
from ..workflows import CandidateDebate__Llm__Matchup
from .mixins import ProjectInput


class MatchupComponent(TableComponent, ProjectInput):
    table = Matchup

    template_names = {
        "entries": "project_management/matchup/table.html",
        "entry": "project_management/matchup/view.html",
        "search": "project_management/matchup/form.html",
        "create": "project_management/matchup/form.html",
    }

    display_name = "Candidate Matchups"
    description_short = (
        "Head-to-head comparisons of two candidates in a project, judged by an "
        "llm debate or by a user. Each result updates both candidates' ratings."
    )

    # Matchups can't be edited, as later ratings are built on top of them
    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
    ]

    @classmethod
    def has_permission(cls, user, component_type, table_entry=None) -> bool:
        # anyone can view & search, and admins or the project's leaders and
        # members can run matchups (checked on submit)
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        return component_type == "create"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "project_id",
        "judge_type",
    ]

    @property
    def candidate_options(self) -> list[tuple[int, str]]:
        # only the candidates of the selected project
        project_id = self.form_data.get("project_id")
        if not project_id:
            return []
        candidates = (
            Candidate.objects.filter(project_id=project_id)
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

    winner_options = [
        ("a", "Candidate A"),
        ("b", "Candidate B"),
        ("draw", "Draw"),
    ]

    def mount_for_create(self):
        self.update_form("judge_type", "llm-debate")

    def refresh_options(self):
        # the candidate options depend on the selected project
        self.js_actions = [
            {"refresh_select2": []},
        ]

    def check_form_for_create(self):
        self.check_required_inputs()
        if self.form_errors:
            return

        user = self.request.user
        project_id = self.form_data["project_id"]
        if not user.is_staff and not Project.objects.filter(
            Q(leaders=user) | Q(members=user),
            id=project_id,
        ):
            self.form_errors.append(
                "Only the project's leaders and members can run matchups."
            )

        candidate_ids = [
            self.form_data.get("candidate_a_id"),
            self.form_data.get("candidate_b_id"),
        ]
        given_ids = [i for i in candidate_ids if i]
        if self.form_data["judge_type"] == "manual":
            if len(given_ids) != 2 or not self.form_data.get("winner"):
                self.form_errors.append(
                    "Manual matchups need both candidates and the winner."
                )
        elif len(given_ids) == 1:
            self.form_errors.append(
                "Give both candidates, or leave both empty to have them picked."
            )
        elif (
            not given_ids
            and Candidate.objects.filter(project_id=project_id).count() < 2
        ):
            self.form_errors.append("The project needs at least two candidates.")

        if len(given_ids) == 2 and given_ids[0] == given_ids[1]:
            self.form_errors.append("The two candidates must be different.")

    def unmount_for_create(self):
        return  # the matchup is made by `Project.record_matchup` instead

    def save_to_db_for_create(self):
        project = Project.objects.get(id=self.form_data["project_id"])
        candidate_a_id = self.form_data.get("candidate_a_id")
        candidate_b_id = self.form_data.get("candidate_b_id")

        if self.form_data["judge_type"] == "llm-debate":
            # the debate is ran by a worker, so the matchup is made later
            self.debate_workitem = CandidateDebate__Llm__Matchup.run_cloud(
                project_id=project.id,
                candidate_a_id=candidate_a_id,
                candidate_b_id=candidate_b_id,
                user_id=self.request.user.id,
            )
        else:
            self.table_entry = project.record_matchup(
                candidate_a=Candidate.objects.get(id=candidate_a_id),
                candidate_b=Candidate.objects.get(id=candidate_b_id),
                score_a={"a": 1.0, "b": 0.0, "draw": 0.5}[self.form_data["winner"]],
                judge_type="manual",
                rationale=self.form_data.get("rationale"),
                user=self.request.user,
            )

    def get_submission_redirect(self):
        # llm debates go to the worker's job, where its progress can be followed
        if self.form_data["judge_type"] == "llm-debate":
            return redirect(
                "data_explorer:table-entry",
                "WorkItem",
                self.debate_workitem.pk,
            )
        return super().get_submission_redirect()
