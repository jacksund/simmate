# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.website.htmx.components import HtmxComponent
from simmate.workflows.utilities import get_all_workflows


class WorkflowSearchForm(HtmxComponent):

    template_name = "workflows/search_form.html"

    tags_options = [
        ## get_all_workflow_types
        # 'customized',
        "diffusion",
        "dynamics",
        "electronic-structure",
        "maintenance",
        "population-analysis",
        "relaxation",
        "restart",
        "static-energy",
        "structure-prediction",
        #
        ## all apps
        "vasp",
        "toolkit",
        "bader",
        "baderkit",
        "quantum-espresso",
    ]

    def mount(self):
        pass
        self.workflows = get_all_workflows()
        self.form_data["recommended_only"] = True

    def submit(self):

        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)
