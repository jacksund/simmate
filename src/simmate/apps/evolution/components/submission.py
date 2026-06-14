# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.config import settings
from simmate.website.htmx.components import HtmxComponent
from simmate.workflows.utils import get_workflow


class FixedCompositionSubmissionComponent(HtmxComponent):

    template_name = "evolution/fixed_composition_submission.html"

    # both set in mount()
    workflow_name: str = None
    workflow: any = None  # Workflow obj

    is_pricing_confirmed: bool = False
    is_submission_confirmed: bool = False

    def mount(self):
        self.workflow_name = self.request.resolver_match.kwargs["workflow_name"]
        self.workflow = get_workflow(self.workflow_name)
        self.form_data["submitted_by_id"] = self.request.user.id
        self.form_data["composition"] = None
        if not settings.website.show_finances:
            self.is_pricing_confirmed = True

    def submit(self):
        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)

    def load_composition(self, **kwargs):
        # The form_data is already populated by HTMX with the 'composition' value.
        pass

    # -------------------------------------------------------------------------

    def confirm_pricing(self):
        self.is_pricing_confirmed = True

    def confirm_submission(self):
        allowed_parameters = self.workflow.parameter_names
        parameters = {
            k: v for k, v in self.form_data.items() if k in allowed_parameters
        }

        self.status = self.workflow.run_cloud(**parameters)

        self.is_submission_confirmed = True
