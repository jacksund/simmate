from django.contrib.auth.models import User
from django.db import transaction

from simmate.database.core import DatabaseTable, table_column

from ..ratings import RATING_SYSTEMS, RatingSystem
from .candidate import Candidate
from .matchup import Matchup


class Leaderboard(DatabaseTable):
    """
    A ranking of candidates for one use, such as "Gaming Phone Batteries" or
    "Mars Entry Heat Shields". Candidates are rated against one another using
    the leaderboard's `objective`, and any kind of candidate can compete (e.g.
    liquid, solid, and nuclear propellants all in one leaderboard).

    Leaderboards form a tree from general to specific, where each child
    leaderboard adds requirements on top of its parent's (e.g. Batteries ›
    Phone Batteries › Gaming Phone Batteries). Projects then pick from them
    through their `ProjectComponent`s.
    """

    class Meta:
        db_table = "project_management__leaderboards"

    # -------------------------------------------------------------------------

    name = table_column.CharField(max_length=50)
    """
    The name of what is being ranked (e.g. "Gaming Phone Batteries"). This
    should read clearly on its own, without its parent leaderboards.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    Any extra context about this leaderboard, such as background, links, or
    how candidates are being found.
    """

    objective = table_column.TextField(blank=True, null=True)
    """
    The ground rules for judging this leaderboard's candidates, i.e. what makes
    one candidate better than another (e.g. "a stable cathode with the highest
    voltage, where cobalt-free options are preferred"). A child leaderboard's
    objective usually builds on its parent's (e.g. "Same as Phone Batteries,
    plus 65 W+ fast charging"). This is what llm debates use, along with the
    `description`, to pick the winner of each matchup.

    Leaderboards that only group others (e.g. "Batteries") can leave this
    empty.
    """

    rating_system_options = list(RATING_SYSTEMS)
    rating_system = table_column.CharField(
        max_length=25,
        blank=True,
        null=True,
        default="glicko",
    )
    """
    How this leaderboard's candidates are rated from their matchups. Must be
    one of `rating_system_options` (see `simmate.apps.project_management.ratings`).
    """

    parent_leaderboard = table_column.ForeignKey(
        "self",
        on_delete=table_column.SET_NULL,
        null=True,
        blank=True,
        related_name="child_leaderboards",
    )
    """
    The more general leaderboard that this one is a more specific version of.
    Leaderboards can be nested any number of levels deep.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        # the leaderboard table links to each parent (one query, not one per row)
        return cls.objects.select_related("parent_leaderboard")

    def get_path(self, max_depth: int = 10) -> list["Leaderboard"]:
        """
        Gives the leaderboards from the top level down to (and including) this
        one, such as for a breadcrumb.

        Args:
            max_depth: The most parent leaderboards to walk up through, which
                also guards against accidental cycles.
        """
        path = [self]
        while path[0].parent_leaderboard_id and len(path) <= max_depth:
            if path[0].parent_leaderboard_id in {board.id for board in path}:
                break  # a cycle
            parent = (
                Leaderboard.objects.filter(id=path[0].parent_leaderboard_id)
                .only("name", "parent_leaderboard_id")
                .first()
            )
            if not parent:
                break
            path.insert(0, parent)
        return path

    # -------------------------------------------------------------------------

    def get_rating_system(self) -> RatingSystem:
        """
        Gives the rating system that this leaderboard's candidates use.
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
        Saves the result of a matchup between two of this leaderboard's
        candidates and updates both of their ratings.

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
            if candidate.leaderboard_id != self.id:
                raise Exception(
                    f"Candidate {candidate.display_id} is not in leaderboard "
                    f"{self.name}."
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
                leaderboard=self,
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
        Resets every candidate's rating and then replays all of this
        leaderboard's matchups in order. This is needed after changing the
        `rating_system`.
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
