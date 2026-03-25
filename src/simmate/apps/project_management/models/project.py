# -*- coding: utf-8 -*-

import random

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column

from ..data import GREEK_GODS


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
