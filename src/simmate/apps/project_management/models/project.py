import random

from django.contrib.auth.models import User

from simmate.config import settings
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
