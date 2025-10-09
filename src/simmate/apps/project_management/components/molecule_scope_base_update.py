# -*- coding: utf-8 -*-

from django.shortcuts import redirect

from simmate.website.core_components.components.dynamic_form import parse_value
from simmate.website.unicorn.components import UnicornView

from ..models import Project


class MoleculeScopeBaseUpdateView(UnicornView):

    template_name = "projects/project/molecule_scope_base_update.html"

    class Meta:
        javascript_exclude = ("project_obj",)

    def mount(self):
        self.project_id = self.request.resolver_match.kwargs["project_id"]
        self.project_obj = Project.objects.get(id=self.project_id)

        # mount the existing values to the form
        starting_config = (
            self.project_obj.molecule_scope_base
            if self.project_obj.molecule_scope_base is not None
            else {}
        )
        for key, value in starting_config.items():
            if hasattr(self, key):
                setattr(self, key, value)

    project_id = None
    project_obj = None

    # These are all optional and all have fixed forms. But in the future,
    # I'd like to allow more advanced customization for fields like
    # functional_groups and reactivity_warnings.

    molecular_weight_exact__gte = None
    molecular_weight_exact__lte = None

    num_stereocenters__gte = None
    num_stereocenters__lte = None

    log_p_rdkit__gte = None
    log_p_rdkit__lte = None

    num_rings__gte = None
    num_rings__lte = None

    num_h_acceptors__gte = None
    num_h_acceptors__lte = None

    num_h_donors__gte = None
    num_h_donors__lte = None

    def submit_form(self):
        # unmount the existing values to the form
        starting_config = (
            self.project_obj.molecule_scope_base
            if self.project_obj.molecule_scope_base is not None
            else {}
        )
        new_scope_config = starting_config.copy()
        for key in [
            "molecular_weight_exact__gte",
            "molecular_weight_exact__lte",
            "num_stereocenters__gte",
            "num_stereocenters__lte",
            "log_p_rdkit__gte",
            "log_p_rdkit__lte",
            "num_rings__gte",
            "num_rings__lte",
            "num_h_acceptors__gte",
            "num_h_acceptors__lte",
            "num_h_donors__gte",
            "num_h_donors__lte",
        ]:
            new_value = parse_value(getattr(self, key))
            if new_value is not None:
                new_scope_config[key] = getattr(self, key)
            else:
                new_scope_config.pop(key, None)
        self.project_obj.molecule_scope_base = new_scope_config
        self.project_obj.save()

        return redirect(
            "data_explorer:table-entry",
            "Project",
            self.project_id,
        )
