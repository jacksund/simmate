from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column


class Candidate(DatabaseTable):
    """
    A substance or mixture that a project is considering, such as a possible
    drug, catalyst, or battery material.

    Each project's candidates are rated against one another to give a
    leaderboard (see `Matchup` and `Project.rating_system`). By default, the
    ratings come from llm debates between pairs of candidates, which are judged
    using the project's `objective` and each candidate's `metadata` and
    `comments`. Other apps can add their results (e.g. experimental or
    computational) to the `metadata` so that later matchups take them into
    account.
    """

    class Meta:
        db_table = "project_management__candidates"
        # Note: there is no unique constraint on (project, substance) because
        # merging two substances that are both candidates of one project would
        # break it. Duplicates are blocked by the web form instead.

    id_prefix = "CAND"
    """
    The static prefix of every candidate's `display_id` (e.g. "CAND-123").
    """

    # -------------------------------------------------------------------------

    project = table_column.ForeignKey(
        "Project",
        on_delete=table_column.CASCADE,
        related_name="candidates",
    )
    """
    The project that this candidate belongs to.
    """

    is_mixture = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether this candidate is a `mixture` (True) or a single `substance` (False).
    Only the matching one of these two columns should be set.
    """

    substance = table_column.ForeignKey(
        "inventory_management.Substance",
        on_delete=table_column.PROTECT,
        related_name="project_candidates",
        blank=True,
        null=True,
    )
    """
    The substance that this candidate is. Only set when `is_mixture=False`.
    """

    mixture = table_column.ForeignKey(
        "inventory_management.Mixture",
        on_delete=table_column.PROTECT,
        related_name="project_candidates",
        blank=True,
        null=True,
    )
    """
    The mixture that this candidate is. Only set when `is_mixture=True`.
    """

    # -------------------------------------------------------------------------

    rating = table_column.FloatField(blank=True, null=True)
    """
    The candidate's current rating, which the project's leaderboard is sorted
    by (higher is better). How this is calculated depends on the project's
    `rating_system`.
    """

    rating_deviation = table_column.FloatField(blank=True, null=True)
    """
    How uncertain the `rating` is, where a candidate's true rating is roughly
    within `rating ± 2 * rating_deviation`. This starts high and shrinks with
    each matchup. Only used by some rating systems (e.g. Glicko), and empty for
    others (e.g. Elo).
    """

    rating_data = table_column.JSONField(blank=True, null=True)
    """
    Any other values that the project's rating system needs to keep for this
    candidate.
    """

    num_matchups = table_column.IntegerField(blank=True, null=True, default=0)
    """
    The number of matchups that this candidate has been a part of.
    """

    # -------------------------------------------------------------------------

    metadata = table_column.JSONField(blank=True, null=True, default=dict)
    """
    Any extra information about this candidate, such as results from other
    apps, given as `{source: data}` (e.g. `{"assay": {"ic50_nM": 12}}`). This
    is given as-is to the judge of each matchup.
    """

    comments = table_column.TextField(blank=True, null=True)
    """
    Notes from project members about this candidate, such as why it was added
    or ideas for it. These are also given to the judge of each matchup.
    """

    added_by = table_column.ForeignKey(
        User,
        on_delete=table_column.SET_NULL,
        related_name="project_candidates_added",
        blank=True,
        null=True,
    )
    """
    The user that added this candidate to the project.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        return cls.objects.select_related(
            "project",
            "substance__molecule",
            "mixture",
        )

    def save(self, *args, **kwargs):
        # new candidates start with the initial rating of their project's
        # rating system
        if self._state.adding and self.rating is None:
            for column, value in (
                self.project.get_rating_system().initial_state().items()
            ):
                setattr(self, column, value)
        super().save(*args, **kwargs)
