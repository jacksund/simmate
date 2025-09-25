# -*- coding: utf-8 -*-

import random

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column

from ..data import GREEK_GODS


class Project(DatabaseTable):
    """
    Project meteadata
    """

    class Meta:
        db_table = "project_management__projects"

    html_display_name = "Projects"
    html_description_short = "List of different chemistry projects"

    html_entries_template = "projects/project/table.html"
    html_entry_template = "projects/project/view.html"

    html_form_view = "project-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

    source = None  # disable col

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

    status_choices = (
        ("PR", "Pending Review"),
        ("A", "Active"),
        ("IA", "Inactive"),
        ("RU", "Requires Update"),
    )
    status = table_column.CharField(
        max_length=3,
        choices=status_choices,
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

    # TODO: options should be pulled from settings file to allow custom setups
    # For now, I put in random placeholders
    discipline_options = [
        "Battery Materials",
        "Pesticides",
        "Photovoltaics",
        "Other",
    ]
    discipline = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    """
    The discipline type associated with. The options here are pulled from
    the simmate settings file. The defaults are made to span many companies
    and labs, so they are more general, whereas individual simmate instances
    may want a more well-defined list.
    """

    # -------------------------------------------------------------------------

    # has related - molecule_scopes

    molecule_scope_base = table_column.JSONField(blank=True, null=True)
    """
    A list of filters to apply when querying all MoleculeScopes.
    (e.g., range of allowed mol wts, max functional groups, etc.)
    """
    # TODO: would I ever want to move this to the MoleculeScope model and
    # allow filters/limit to vary on a per-molecule-scope basis? I don't do this
    # for now, because it's easier on users to just have a universal default.

    # -------------------------------------------------------------------------

    @classmethod
    def suggest_new_name(cls) -> str:

        suggested_names = list(GREEK_GODS["name-english"])
        existing_names = list(cls.objects.values_list("name", flat=True).all())

        suggested_names_cleaned = [
            n for n in suggested_names if n not in existing_names
        ]
        return random.choice(suggested_names_cleaned)

    # -------------------------------------------------------------------------

    html_tabtitle_label_col = "name"

    @classmethod
    def get_web_queryset(cls):
        return cls.objects.prefetch_related("leaders")

    @property
    def html_extra_entry_context(self) -> dict:

        count_limit = 50_000

        tags__limit = 10
        tags__count = self.tags.all()[:count_limit].count()
        tags = self.tags.order_by("-id").all()[:tags__limit]
        tags__truncated = bool(len(tags) >= tags__limit)

        hypotheses__limit = 10
        hypotheses__count = self.hypotheses.all()[:count_limit].count()
        hypotheses = (
            self.hypotheses.prefetch_related("tags")
            .select_related("created_by", "driven_by")
            .order_by("-id")
            .all()[:hypotheses__limit]
        )
        hypotheses__truncated = bool(len(hypotheses) >= hypotheses__limit)

        return {
            "tags": tags,
            "tags__count": tags__count,
            "tags__truncated": tags__truncated,
            "hypotheses": hypotheses,
            "hypotheses__count": hypotheses__count,
            "hypotheses__truncated": hypotheses__truncated,
        }

    # -------------------------------------------------------------------------
