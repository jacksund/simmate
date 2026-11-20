from django.db.models import Q

from simmate.apps.inventory_management.models import Mixture, Substance
from simmate.website.data_explorer.components import TableComponent

from ..models import Candidate, Matchup
from .mixins import LeaderboardInput


class CandidateComponent(TableComponent, LeaderboardInput):
    table = Candidate

    template_names = {
        "entries": "project_management/candidate/table.html",
        "entry": "project_management/candidate/view.html",
        "search": "project_management/candidate/form.html",
        "create": "project_management/candidate/form.html",
        "update": "project_management/candidate/form.html",
    }

    display_name = "Candidates"
    description_short = (
        "The substances and mixtures that a leaderboard is considering. "
        "Candidates are rated against one another (e.g. through llm debates) "
        "to rank them for the leaderboard's objective."
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
        # anyone can view & search, any signed-in user can add candidates, and
        # admins or the user that added a candidate can edit it
        if component_type in ["dashboard", "entries", "entry", "report", "search"]:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or component_type == "create":
            return True
        if component_type == "update":
            return table_entry.added_by_id == user.id
        return False

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Candidate) -> dict:
        limit = 25
        matchups = (
            Matchup.get_web_queryset()
            .filter(Q(candidate_a=table_entry) | Q(candidate_b=table_entry))
            .order_by("-created_at")
        )
        return {
            "matchups": matchups[:limit],
            "matchups__count": table_entry.num_matchups,
            "matchups__truncated": table_entry.num_matchups > limit,
        }

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "leaderboard_id",
        "is_mixture",
        # "substance_id",  # only if is_mixture=False
        # "mixture_id",  # only if is_mixture=True
    ]

    def mount_for_create(self):
        self.update_form("is_mixture", False)

    def check_form_for_create(self):
        self.check_required_inputs()
        if self.form_errors:
            return

        leaderboard_id = self.form_data["leaderboard_id"]

        # Substances and mixtures are typed in by their IDs, so these are
        # looked up and swapped for the real database IDs here
        if self.form_data["is_mixture"]:
            self.form_data["substance_id"] = None
            try:
                mixture = Mixture.get_by_display_id(
                    str(self.form_data.get("mixture_id") or "")
                )
            except Mixture.DoesNotExist:
                self.form_errors.append(
                    "'mixture_id' must be the ID of an existing mixture (e.g. BCDF-123)."
                )
                return
            self.form_data["mixture_id"] = mixture.id
            existing = Candidate.objects.filter(
                leaderboard_id=leaderboard_id,
                mixture=mixture,
            )
        else:
            self.form_data["mixture_id"] = None
            try:
                # this follows merged IDs and loads datastore-only substances
                substance = Substance.get_by_id(
                    str(self.form_data.get("substance_id") or "")
                )
            except Substance.DoesNotExist:
                self.form_errors.append(
                    "'substance_id' must be the ID of an existing substance "
                    "(e.g. BCD-012-3456)."
                )
                return
            self.form_data["substance_id"] = substance.id
            existing = Candidate.objects.filter(
                leaderboard_id=leaderboard_id,
                substance=substance,
            )

        if existing.exists():
            self.form_errors.append(
                "This is already a candidate of the leaderboard "
                f"({existing.first().display_id})."
            )

    def unmount_for_create(self):
        super().unmount_for_create()
        self.table_entry.added_by = self.request.user

    # -------------------------------------------------------------------------

    # UPDATE

    # only the notes can be changed. Ratings come from matchups, and the
    # leaderboard or substance can't be swapped once matchups exist.
    mount_for_update_columns = [
        "comments",
    ]

    def check_form_for_update(self):
        return  # nothing is required
