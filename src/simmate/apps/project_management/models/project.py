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

    html_entries_template = "project_management/project/table.html"
    html_entry_template = "project_management/project/view.html"

    html_form_component = "project-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

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

    parent_project = table_column.ForeignKey(
        "self",
        on_delete=table_column.SET_NULL,
        null=True,
        blank=True,
        related_name="child_projects",
    )

    num_child_projects_recursive = table_column.IntegerField(blank=True, null=True)
    # a fully iterated version (children + their children)

    is_top_level = table_column.BooleanField(blank=True, null=True)
    # True when "parent_project" is null

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

        return {
            "tags": tags,
            "tags__count": tags__count,
            "tags__truncated": tags__truncated,
        }

    # -------------------------------------------------------------------------

    # This section is DEPRECIATED in favor of form mix-ins

    @property
    def tag_options(self) -> list[tuple]:

        from .tag import Tag

        # query for all tags directly linked
        project_tags = self.tags.order_by("name").values_list("id", "name").all()

        # add in generic tags after specific ones
        generic_tags = (
            Tag.objects.filter(tag_type="all-projects")
            .order_by("name")
            .values_list("id", "name")
            .all()
        )

        # reformat into tuple of (value, display)
        return [
            (id, tag_name) for id, tag_name in list(project_tags) + list(generic_tags)
        ]

    @classmethod
    @property
    def project_options(cls) -> list[tuple]:

        # query for all tags
        projects = cls.objects.order_by("name").values_list("id", "name").all()

        # reformat into tuple of (value, display)
        return [(id, name) for id, name in projects]

    # -------------------------------------------------------------------------
