# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .project import Project


class Tag(DatabaseTable):

    class Meta:
        db_table = "project_management__tags"

    html_display_name = "Tags, Labels, & Categories"
    html_description_short = (
        "Labels that help with organizing Project items "
        "like hypotheses, targets, & orders. "
    )

    html_entries_template = "project_management/tag/table.html"
    html_entry_template = "project_management/tag/view.html"

    html_form_component = "tag-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

    # TODO: Maybe allow FilteredScope objects to be linked to these for
    # auto-tagging things in other tables

    tag_type_options = [
        "project-specific",
        "all-projects",
    ]
    tag_type = table_column.CharField(max_length=30, blank=True, null=True)
    """
    Whether the tag is project-specific or for all projects
    """

    project = table_column.ForeignKey(
        Project,
        on_delete=table_column.PROTECT,
        related_name="tags",
        blank=True,
        null=True,
    )

    name = table_column.CharField(max_length=30, blank=True, null=True)
    """
    A short nickname given to the tag.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    A short 1-2 sentence description of the tag
    """
