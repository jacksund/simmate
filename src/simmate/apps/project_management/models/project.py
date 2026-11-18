import random

from django.contrib.auth.models import User
from django.db import transaction

from simmate.config import settings
from simmate.database.core import DatabaseTable, table_column

from ..data import GREEK_GODS
from ..ratings import RATING_SYSTEMS, RatingSystem
from .candidate import Candidate
from .matchup import Matchup


class Project(DatabaseTable):
    """
    Project meteadata
    """

    class Meta:
        db_table = "project_management__projects"

    # -------------------------------------------------------------------------

    name = table_column.CharField(max_length=25)
    """
    The short-hand project name (ex: "Zeus")
    """

    description = table_column.TextField(blank=True, null=True)
    """
    A full description of this project, including its goals, scope, member roles,
    and updates. Note, this is a free-text field and it's up to the leaders
    to fill out this information & how much detail they wish to provide
    """

    objective = table_column.TextField(blank=True, null=True)
    """
    The ground rules for judging this project's candidates, i.e. what makes one
    candidate better than another (e.g. "a stable cathode with the highest
    voltage, where cobalt-free options are preferred"). This is what llm
    debates use, along with the `description`, to pick the winner of each
    matchup.
    """

    rating_system_options = list(RATING_SYSTEMS)
    rating_system = table_column.CharField(
        max_length=25,
        blank=True,
        null=True,
        default="glicko",
    )
    """
    How this project's candidates are rated from their matchups. Must be one
    of `rating_system_options` (see `simmate.apps.project_management.ratings`).
    """

    status_options = (
        "Under Review",
        "Active",
        "Inactive",
        "Requires Update",
        "Staged for Deletion",
    )
    status = table_column.CharField(
        max_length=25,
        blank=True,
        null=True,
    )
    """
    The current status of the project. 
    
    If an "Active" project goes 12 months without any updates, it is reverted 
    to "Requires Update". Another 6 months and it is reverted to "Inactive".
    """

    leaders = table_column.ManyToManyField(
        User,
        related_name="projects_as_leader",
    )
    """
    All users that are "leaders" of this project
    """

    members = table_column.ManyToManyField(
        User,
        related_name="projects_as_member",
    )
    """
    All users that are "members" of this project. This is very flexible and
    can be generalized as any person participating and needing this project's
    data.
    """

    discipline_options = settings.project_management.discipline_options
    discipline = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    """
    The research area this project belongs to. The options are pulled from
    the simmate settings file (`project_management.discipline_options`). The
    defaults are general so they span many companies and labs, whereas
    individual simmate instances may want a more well-defined list.
    """

    # -------------------------------------------------------------------------

    parent_project = table_column.ForeignKey(
        "self",
        on_delete=table_column.SET_NULL,
        null=True,
        blank=True,
        related_name="child_projects",
    )
    """
    The project that this one is a part of (i.e. a sub-project of). Projects
    can be nested any number of levels deep to allow folder-like organization.
    """

    num_child_projects_recursive = table_column.IntegerField(blank=True, null=True)
    # a fully iterated version (children + their children)

    is_top_level = table_column.BooleanField(blank=True, null=True)
    # True when "parent_project" is null

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        # the project table links to each parent (one query, not one per row)
        return cls.objects.select_related("parent_project")

    @classmethod
    def suggest_new_name(cls) -> str:

        suggested_names = list(GREEK_GODS["name-english"])
        existing_names = list(cls.objects.values_list("name", flat=True).all())

        suggested_names_cleaned = [
            n for n in suggested_names if n not in existing_names
        ]
        return random.choice(suggested_names_cleaned)

    def get_path(self, max_depth: int = 10) -> list["Project"]:
        """
        Gives the projects from the top level down to (and including) this
        one, such as for a breadcrumb.

        Args:
            max_depth: The most parent projects to walk up through, which
                also guards against accidental cycles.
        """
        path = [self]
        while path[0].parent_project_id and len(path) <= max_depth:
            if path[0].parent_project_id in {project.id for project in path}:
                break  # a cycle
            parent = (
                Project.objects.filter(id=path[0].parent_project_id)
                .only("name", "parent_project_id")
                .first()
            )
            if not parent:
                break
            path.insert(0, parent)
        return path

    # -------------------------------------------------------------------------

    def get_rating_system(self) -> RatingSystem:
        """
        Gives the rating system that this project's candidates use.
        """
        return RATING_SYSTEMS[self.rating_system or "glicko"]()

    def record_matchup(
        self,
        candidate_a: Candidate,
        candidate_b: Candidate,
        score_a: float,
        judge_type: str,
        rationale: str = None,
        user: User = None,
    ) -> Matchup:
        """
        Saves the result of a matchup between two of this project's candidates
        and updates both of their ratings.

        Args:
            candidate_a: The first candidate of the matchup.
            candidate_b: The second candidate of the matchup.
            score_a: The result for candidate A, where 1 is a win, 0.5 is a
                draw, and 0 is a loss.
            judge_type: How the winner was decided. Must be one of
                `Matchup.judge_type_options`.
            rationale: Why the winner was picked.
            user: The user that ran or judged the matchup.

        Returns:
            The new `Matchup`.
        """
        for candidate in [candidate_a, candidate_b]:
            if candidate.project_id != self.id:
                raise Exception(
                    f"Candidate {candidate.display_id} is not in project {self.name}."
                )
        if candidate_a.id == candidate_b.id:
            raise Exception("A candidate can't be matched up against itself.")

        with transaction.atomic():
            # Debates can run in parallel (and take a while), so we reload both
            # candidates with a lock to update their latest ratings
            locked = Candidate.objects.select_for_update().in_bulk(
                [candidate_a.id, candidate_b.id]
            )
            candidate_a = locked[candidate_a.id]
            candidate_b = locked[candidate_b.id]

            ratings_before = Matchup.get_ratings_snapshot(candidate_a, candidate_b)
            self.get_rating_system().update(candidate_a, candidate_b, score_a)
            candidate_a.num_matchups += 1
            candidate_b.num_matchups += 1
            for candidate in [candidate_a, candidate_b]:
                candidate.save()
            return Matchup.objects.create(
                project=self,
                candidate_a=candidate_a,
                candidate_b=candidate_b,
                score_a=score_a,
                judge_type=judge_type,
                rationale=rationale,
                judged_by=user,
                ratings_before=ratings_before,
                ratings_after=Matchup.get_ratings_snapshot(candidate_a, candidate_b),
            )

    def recalculate_ratings(self):
        """
        Resets every candidate's rating and then replays all of this project's
        matchups in order. This is needed after changing the `rating_system`.
        """
        rating_system = self.get_rating_system()
        candidates = {c.id: c for c in self.candidates.all()}
        for candidate in candidates.values():
            for column, value in rating_system.initial_state().items():
                setattr(candidate, column, value)
            candidate.num_matchups = 0

        matchups = list(self.matchups.order_by("created_at", "id"))
        for matchup in matchups:
            candidate_a = candidates[matchup.candidate_a_id]
            candidate_b = candidates[matchup.candidate_b_id]
            matchup.ratings_before = Matchup.get_ratings_snapshot(
                candidate_a, candidate_b
            )
            rating_system.update(candidate_a, candidate_b, matchup.score_a)
            candidate_a.num_matchups += 1
            candidate_b.num_matchups += 1
            matchup.ratings_after = Matchup.get_ratings_snapshot(
                candidate_a, candidate_b
            )

        with transaction.atomic():
            Candidate.objects.bulk_update(
                candidates.values(),
                ["rating", "rating_deviation", "rating_data", "num_matchups"],
            )
            Matchup.objects.bulk_update(matchups, ["ratings_before", "ratings_after"])

    # -------------------------------------------------------------------------
