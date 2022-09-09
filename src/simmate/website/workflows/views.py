# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from simmate.database.base_data_types import DatabaseTable
from simmate.website.core_components.base_api_view import SimmateAPIViewSet
from simmate.website.workflows.forms import SubmitWorkflow
from simmate.workflows.utilities import (  # WORKFLOW_TYPES,
    get_calculators_by_type,
    get_workflow,
    get_workflow_names_by_type,
)

TYPE_DESCRIPTIONS = {
    "static-energy": (
        "Calculate the energy for a structure. In many cases, this also "
        "involves calculating the lattice strain and forces for each site."
    ),
    "relaxation": (
        "Geometry-optimize a structure's the lattice and sites "
        "to their lowest-energy positions until convergence criteria are met."
    ),
    "population-analysis": (
        "Evaluate where electrons exist in a structure and assign them to a "
        "specific site/atom. Used to predicted oxidation states."
    ),
    # "band-structure": (
    #     "These workflows calculate the electronic band structure for a material."
    # ),
    # "density-of-states": (
    #     "These workflows calculate the electronic density of states for a material."
    # ),
    "dynamics": (
        "Run a molecular dynamics simulation for a material. Involves "
        "iteratively evaluating the energy/forces at "
        "specific temperature (or temperature ramp)."
    ),
    # "diffusion": (
    #     "These workflows evaluate the diffusion of an atom through a material. "
    #     "At this time, these workflows are entirely Nudged-Elastic-Band (NEB) "
    #     "calculations."
    # ),
}


def workflows_all(request):

    # TODO: maybe instead load these descriptions from the simmate.{module}'s docstr
    # This would look something like...
    # all_metadata = {}
    # for flow_type in WORKFLOW_TYPES:
    #     --> grab the module
    #     --> use the __doc__ as the text.

    # now let's put the data and template together to send the user
    context = {"workflows_metadata": TYPE_DESCRIPTIONS}
    template = "workflows/all.html"
    return render(request, template, context)


def workflows_by_type(request, workflow_type):

    calculators = get_calculators_by_type(workflow_type)

    # pull the information together for each individual flow and organize by
    # workflow calculator.
    workflow_dict = {}
    for calculator in calculators:
        workflow_names = get_workflow_names_by_type(workflow_type, calculator)
        workflow_dict[calculator] = [get_workflow(n) for n in workflow_names]

    # now let's put the data and template together to send the user
    context = {
        "workflow_type": workflow_type,
        "workflow_type_description": TYPE_DESCRIPTIONS.get(workflow_type, ""),
        "workflow_dict": workflow_dict,
    }
    template = "workflows/by_type.html"
    return render(request, template, context)


class WorkflowAPIViewSet(SimmateAPIViewSet):

    template_list = "workflows/detail.html"
    template_retrieve = "workflows/detail_run.html"

    @staticmethod
    def get_table(
        request,
        workflow_type,
        workflow_calculator,
        workflow_preset,
        pk=None,  # this is passed for 'retrieve' views but we don't use it
    ) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        name_full = f"{workflow_type}.{workflow_calculator}.{workflow_preset}"
        workflow = get_workflow(name_full)
        return workflow.database_table

    @staticmethod
    def get_initial_queryset(
        request,
        workflow_type,
        workflow_calculator,
        workflow_preset,
        pk=None,  # this is passed for 'retrieve' views but we don't use it
    ):
        name_full = f"{workflow_type}.{workflow_calculator}.{workflow_preset}"
        workflow = get_workflow(name_full)
        return workflow.all_results

    def get_list_context(
        self,
        request,
        workflow_type,
        workflow_calculator,
        workflow_preset,
    ) -> dict:

        name_full = f"{workflow_type}.{workflow_calculator}.{workflow_preset}"
        workflow = get_workflow(name_full)

        # TODO: grab some metadata about this calc. For example...
        # ncalculations = MITRelaxation.objects.count()
        # nflows_submitted = workflow.nflows_submitted

        return {
            "workflow": workflow,
            "flow_id": None,  # TODO
            "nflows_submitted": None,
        }

    def get_retrieve_context(
        self,
        request,
        workflow_type,
        workflow_calculator,
        workflow_preset,
        pk,
    ) -> dict:

        name_full = f"{workflow_type}.{workflow_calculator}.{workflow_preset}"
        workflow = get_workflow(name_full)

        return {"workflow": workflow}


@login_required
def workflow_submit(
    request,
    workflow_type: str,
    workflow_calculator: str,
    workflow_preset: str,
):

    name_full = f"{workflow_type}.{workflow_calculator}.{workflow_preset}"
    workflow = get_workflow(name_full)

    # dynamically create the form for this workflow
    FormClass = SubmitWorkflow.from_workflow(workflow)

    if request.method == "POST":
        submission_form = FormClass(request.POST, request.FILES)

        # To help with debugging:
        # raise Exception(str(submission_form.errors))

        if submission_form.is_valid():

            # We can now submit the workflow for the structure.
            flow_run_id = workflow.run_cloud(
                wait_for_run=False,
                **submission_form.cleaned_data,
            )

            return redirect(f"https://cloud.prefect.io/simmate/flow-run/{flow_run_id}")
    else:
        submission_form = FormClass()
    # now let's put the data and template together to send the user
    context = {
        "workflow": workflow,
        "submission_form": submission_form,
    }
    template = "workflows/submit.html"
    return render(request, template, context)
