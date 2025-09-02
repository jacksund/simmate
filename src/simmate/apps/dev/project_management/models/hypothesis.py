# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column

from .hypothesis_tag import HypothesisTag
from .project import Project


class Hypothesis(DatabaseTable):
    """
    A hypothesis within the project
    """

    html_display_name = "Hypotheses"
    html_description_short = (
        "General hypotheses for Projects. "
        "Each can link to various target compounds & orders."
    )

    html_entries_template = "projects/hypothesis/table.html"
    html_entry_template = "projects/hypothesis/view.html"

    html_form_view = "hypothesis-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

    project = table_column.ForeignKey(
        Project,
        on_delete=table_column.PROTECT,
        related_name="hypotheses",
        blank=True,
        null=True,
    )

    # DEPREC IN FAVOR OF M2M RELATION BELOW
    tag = table_column.ForeignKey(
        HypothesisTag,
        on_delete=table_column.PROTECT,
        related_name="hypotheses",
        blank=True,
        null=True,
    )

    tags = table_column.ManyToManyField(
        "projects.Tag",
        blank=True,
        db_table="project_management__hypotheses__tags_ref",
        related_name="hypotheses",
    )
    """
    Any tags/labels applied to the entry
    """

    created_by = table_column.ForeignKey(
        User,
        related_name="hypotheses_created",
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
    )
    """
    Name of the person that created the hypothesis originally
    """

    driven_by = table_column.ForeignKey(
        User,
        related_name="hypotheses_driven",
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
    )
    """
    Name of the person that is currently leading (or "driving") the evalution
    of the hypothesis
    """

    status_choices = (
        ("PR", "Pending Review"),
        ("A", "Active"),
        ("IA", "Inactive"),
        ("RU", "Requires Update"),
        ("SFD", "Staged for Deletion"),
    )
    status = table_column.CharField(
        blank=True,
        null=True,
    )
    """
    The current status of the scope.
    """

    name = table_column.CharField(max_length=55, blank=True, null=True)
    """
    A short nickname given to the hypothesis by project members. To keep this
    short and effective, it can't be more than 30 characters.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    A short 1-2 sentence description of the hypothesis
    """

    comments = table_column.TextField(blank=True, null=True)
    """
    Any extra comments about this scope. Should include outlook and summary
    of results -- such as why the hypothesis is marked as completed or closed.
    """

    # TODO: add either JSONField or ManyToMany for HypothesisTags
    #   from .hypothesis_tag import HypothesisTag
    # Or should this be a foreign key to HypothesisTag for simplicity?
