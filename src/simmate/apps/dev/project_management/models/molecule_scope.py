# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column

from .project import Project


class MoleculeScope(DatabaseTable):
    """
    A SMARTS query or some substructure search to be applied to a Project
    """

    # TODO: should there be a 2D/3D smilarity scope instead of just smarts query?

    html_form_view = "molecule-scope-form"
    html_enabled_forms = [
        "create",
        "update",
    ]

    project = table_column.ForeignKey(
        Project,
        on_delete=table_column.PROTECT,
        related_name="molecule_scopes",
        blank=True,
        null=True,
    )

    created_by = table_column.ForeignKey(
        User,
        related_name="molecule_scopes_created",
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
    )
    """
    Name of the person that created the molecule scope originally
    """

    driven_by = table_column.ForeignKey(
        User,
        related_name="molecule_scopes_driven",
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
    )
    """
    Name of the person that is currently leading (or "driving") the evalution
    of the molecule scope
    """

    status_choices = (
        ("PR", "Pending Review"),
        ("A", "Active"),
        ("IA", "Inactive"),
        ("RU", "Requires Update"),
        ("SFD", "Staged for Deletion"),
    )
    status = table_column.CharField(
        max_length=3,
        choices=status_choices,
        blank=True,
        null=True,
    )
    """
    The current status of the scope.
    """

    nickname = table_column.CharField(max_length=30, blank=True, null=True)
    """
    A short nickname given to the scope by project members. To keep this
    short and effective, it can't be more than 15 characters.
    """

    # molecule_query_original = table_column.TextField(blank=True, null=True)
    # """
    # The original input SMARTS query. See the `smarts` column for the standardized
    # and cleaned version of this.
    # """

    molecule_query = table_column.TextField(blank=True, null=True)
    """
    The molecular query in SMARTS format. Without any special syntax, this
    would just be a SMILES substructure.
    
    Helpful info:
        - [SMILES docs](https://daylight.com/dayhtml/doc/theory/theory.smiles.html)
        - [SMARTS docs](https://www.daylight.com/dayhtml/doc/theory/theory.smarts.html)
    """

    # sdf = table_column.TextField(blank=True, null=True)
    # """
    # The SMARTS query in SDF format. This is typically used only for rendering images
    # """

    description = table_column.TextField(blank=True, null=True)
    """
    A short 1-2 description of this molecule scope
    """

    comments = table_column.TextField(blank=True, null=True)
    """
    Any extra comments about this scope
    """
