# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.toolkit import Structure
from simmate.website.htmx.components import HtmxComponent
from simmate.workflows.base_flow_types import Workflow
from simmate.workflows.utilities import get_workflow


class WorkflowSubmissionForm(HtmxComponent):

    template_name = "workflows/submission_form.html"

    # both set in mount()
    workflow_name: str = None
    workflow: Workflow = None

    # if "structure" in self.workflow.parameter_names:
    #     self.form_data["structure_input_type"] = "database"
    # structure_input_type_options = [
    #     ("database", "Database"),
    #     ("file", "File"),
    #     ("prototype", "Prototype"),
    #     ("random", "Random"),
    # ]

    database_table_options = [
        ("matproj", "Materials Project"),
        ("jarvis", "JARVIS"),
        ("aflow", "AFLOW"),
    ]

    is_structure_confirmed: bool = False
    is_pricing_confirmed: bool = False
    is_submission_confirmed: bool = False

    def mount(self):

        self.workflow_name = self.request.resolver_match.kwargs["workflow_name"]
        self.workflow = get_workflow(self.workflow_name)
        self.form_data["submitted_by_id"] = self.request.user.id

    # def post_parse(self):
    #     # BUG: checkbox field does not show in POST data when =False. This is
    #     # normal HTML behavior to save on bandwidth, but causes a bug here.
    #     if "recommended_only" not in self.post_data.keys():
    #         self.post_data["recommended_only"] = False

    def submit(self):
        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)

    # -------------------------------------------------------------------------

    def confirm_structure(self):
        self.is_structure_confirmed = True

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

    def on_change_hook__structure_file(self):

        structure = self.form_data.pop("structure_file")

        if not isinstance(structure, Structure):
            raise Exception("Non-structure file provided")

        self.form_data["structure"] = structure

        self.js_actions = [
            {
                "add_threejs_render": [
                    "submission_form_structure",
                    structure.to_threejs_json(),  # TODO: use kwargs
                ]
            }
        ]
