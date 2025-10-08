# -*- coding: utf-8 -*-

from django.shortcuts import redirect

from simmate.website.core_components.components import DynamicFormComponent, UserInput

from ..models import MoleculeScope, Project


class MoleculeScopeFormView(DynamicFormComponent, UserInput):

    template_name = "projects/molecule_scope/form.html"
    table = MoleculeScope

    # -------------------------------------------------------------------------

    project_id = None  # set by mount() via GET args or database value
    project_obj = None  # set by mount()

    driven_by_id = None
    created_by_id = None

    status = None
    status_options = MoleculeScope.status_choices

    molecule_query = None
    # TODO: check if molecule_query is valid with Molecule.from_smarts()

    nickname = None
    description = None
    comments = None

    # -------------------------------------------------------------------------

    required_inputs = [
        "project_id",
        "driven_by_id",
        "created_by_id",
        "status",
        "molecule_query",
        "nickname",
        "description",
    ]

    class Meta:
        javascript_exclude = (
            "status_options",
            "project_obj",
            *UserInput.Meta.javascript_exclude,
            *DynamicFormComponent.Meta.javascript_exclude,
        )

    def mount_extra(self):
        if not self.driven_by_id:
            self.driven_by_id = self.request.user.id
        if not self.created_by_id:
            self.created_by_id = self.request.user.id

        self.project_obj = Project.objects.get(id=self.project_id)

    def get_submission_redirect(self):
        # send back to the project view page
        return redirect(
            "data_explorer:table-entry",
            Project.table_name,
            self.project_id,
        )

    # -------------------------------------------------------------------------
