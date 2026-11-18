from simmate.database.core import DatabaseTable, table_column


class ProjectComponent(DatabaseTable):
    """
    One need of a project (e.g. the "Battery" of a phone build) and the
    leaderboard it picks from. Once a pick is made, it is saved as the
    `chosen_candidate`, which can differ from the leaderboard's top candidate
    (e.g. because of supply or cost).
    """

    class Meta:
        db_table = "project_management__project_components"

    # -------------------------------------------------------------------------

    project = table_column.ForeignKey(
        "Project",
        on_delete=table_column.CASCADE,
        related_name="components",
    )
    """
    The project that needs this component.
    """

    name = table_column.CharField(max_length=50)
    """
    What this component is within the project (e.g. "Battery" or "Cover
    glass").
    """

    leaderboard = table_column.ForeignKey(
        "Leaderboard",
        on_delete=table_column.PROTECT,
        related_name="project_components",
    )
    """
    The leaderboard that this component's candidates are ranked in.
    """

    chosen_candidate = table_column.ForeignKey(
        "Candidate",
        on_delete=table_column.SET_NULL,
        related_name="project_components",
        blank=True,
        null=True,
    )
    """
    The candidate that the project picked for this component. This must be a
    candidate of the `leaderboard`, and is empty until a pick is made.
    """

    notes = table_column.TextField(blank=True, null=True)
    """
    Any notes about this component, such as why the chosen candidate isn't the
    leaderboard's top one.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_web_queryset(cls):
        return cls.objects.select_related(
            "project",
            "leaderboard",
            "chosen_candidate",
        )
