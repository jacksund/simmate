# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.config import settings
from simmate.website.htmx.components import HtmxComponent, StructureInput
from simmate.workflows.utils import get_workflow


class WorkflowSubmissionComponent(HtmxComponent, StructureInput):

    template_name = "workflow_explorer/submission_form.html"

    # both set in mount()
    workflow_name: str = None
    workflow: any = None  # Workflow obj

    database_table_options = [
        ("AflowStructure", "AFLOW"),
        ("CodStructure", "COD"),
        ("JarvisStructure", "JARVIS"),
        ("MatprojStructure", "Materials Project"),
        ("OqmdStructure", "OQMD"),
        # TODO: consider pulling dynamically to include tables of past workflow results
    ]

    is_structure_confirmed: bool = False
    is_pricing_confirmed: bool = False
    is_submission_confirmed: bool = False

    def mount(self):

        self.workflow_name = self.request.resolver_match.kwargs["workflow_name"]
        self.workflow = get_workflow(self.workflow_name)
        self.form_data["submitted_by_id"] = self.request.user.id

    def submit(self):
        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)

    # -------------------------------------------------------------------------

    def confirm_structure(self):
        self.is_structure_confirmed = True
        if not settings.website.show_finances:
            self.is_pricing_confirmed = True

    def confirm_pricing(self):
        self.is_pricing_confirmed = True

    def confirm_submission(self):

        allowed_parameters = self.workflow.parameter_names
        parameters = {
            k: v for k, v in self.form_data.items() if k in allowed_parameters
        }

        self.status = self.workflow.run_cloud(**parameters)

        # TODO: add USDC transaction

        self.is_submission_confirmed = True

    # -------------------------------------------------------------------------

    def on_change_hook__structure__file(self):
        self.load_structure("structure")
