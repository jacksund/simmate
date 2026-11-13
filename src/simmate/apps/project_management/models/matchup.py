from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column


class Matchup(DatabaseTable):
    """
    A head-to-head comparison of two candidates in a project, where the result
    updates both of their ratings (see `Project.record_matchup`).

    The winner is decided either by an llm debate, which judges the two
    candidates using the project's `objective`, or manually by a user.
    """

    class Meta:
        db_table = "project_management__matchups"

    id_prefix = "MATCH"
    """
    The static prefix of every matchup's `display_id` (e.g. "MATCH-123").
    """

    # -------------------------------------------------------------------------

    project = table_column.ForeignKey(
        "Project",
        on_delete=table_column.CASCADE,
        related_name="matchups",
    )
    """
    The project that both candidates belong to.
    """

    candidate_a = table_column.ForeignKey(
        "Candidate",
        on_delete=table_column.CASCADE,
        related_name="matchups_as_a",
    )
    """
    The first candidate of the matchup.
    """

    candidate_b = table_column.ForeignKey(
        "Candidate",
        on_delete=table_column.CASCADE,
        related_name="matchups_as_b",
    )
    """
    The second candidate of the matchup.
    """

    score_a = table_column.FloatField(blank=True, null=True)
    """
    The result for candidate A, where 1 is a win, 0.5 is a draw, and 0 is a
    loss (i.e. a win for candidate B).
    """

    # -------------------------------------------------------------------------

    judge_type_options = [
        "llm-debate",
        "manual",
    ]
    judge_type = table_column.CharField(max_length=25, blank=True, null=True)
    """
    How the winner was decided. Must be one of `judge_type_options`.
    """

    rationale = table_column.TextField(blank=True, null=True)
    """
    Why the winner was picked, such as the llm's argument or a user's note.
    """

    judged_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="project_matchups",
        blank=True,
        null=True,
    )
    """
    The user that ran (for llm debates) or judged (for manual ones) the matchup.
    """

    ratings_before = table_column.JSONField(blank=True, null=True)
    """
    Both candidates' rating columns from right before this matchup, given as
    `{"a": {"rating": ..., "rating_deviation": ...}, "b": {...}}`.
    """

    ratings_after = table_column.JSONField(blank=True, null=True)
    """
    Both candidates' rating columns from right after this matchup (same format
    as `ratings_before`).
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        return cls.objects.select_related(
            "project",
            "candidate_a__substance",
            "candidate_a__mixture",
            "candidate_b__substance",
            "candidate_b__mixture",
        )

    @staticmethod
    def get_ratings_snapshot(candidate_a, candidate_b) -> dict:
        """
        Gives the current rating columns of both candidates, as stored in
        `ratings_before` and `ratings_after`.
        """
        return {
            key: {
                "rating": candidate.rating,
                "rating_deviation": candidate.rating_deviation,
            }
            for key, candidate in [("a", candidate_a), ("b", candidate_b)]
        }

    @property
    def winner(self):
        """
        Gives the candidate that won, or None for a draw.
        """
        if self.score_a == 0.5:
            return None
        return self.candidate_a if self.score_a > 0.5 else self.candidate_b
