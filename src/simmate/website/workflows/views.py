# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from simmate.configuration import settings
from simmate.website.workflows.forms import SubmitWorkflow
from simmate.workflows.utilities import (
    get_apps_by_type,
    get_workflow,
    get_workflow_names_by_type,
)

DEFAULT_TYPE_DESCRIPTIONS = {
    "diffusion": (
        "Evaluate the diffusion of an atom through a material. "
        "At this time, these workflows are entirely Nudged-Elastic-Band (NEB) "
        "calculations."
    ),
    "dynamics": (
        "Molecular dynamics (MD) simulations for a material. Involves "
        "iteratively evaluating the energy/forces at "
        "specific temperature (or temperature ramp)."
    ),
    "electronic-structure": (
        "Calculate the electronic structure for a material. "
        "This include band-structure and density of states calculations."
    ),
    "physical-property": ("Calculate common physical properties."),
    "population-analysis": (
        "Evaluate where electrons exist in a structure and assign them to a "
        "specific site/atom. Used to predicted oxidation states."
    ),
    "relaxation": (
        "Geometry-optimize a structure's the lattice and sites "
        "to their lowest-energy positions until convergence criteria are met."
    ),
    "similarity": ("Run 2D and 3D structure searches across billions of compounds."),
    "solubility": ("Calculate solubility of compounds in different solutions."),
    "stability": (
        "Calculate therodynamic and kinetic stability of compounds, "
        "as well as expected decomposition products."
    ),
    "static-energy": (
        "Calculate the energy for a structure. In many cases, this also "
        "involves calculating the lattice strain and forces for each site."
    ),
    "structure-prediction": (
        "Predict the most stable structure when given only chemical composition "
        "or system. Strategies range from evolutionary searches to "
        "substituition of known materials."
    ),
    # TYPES BELOW ARE UNUSED RIGHT NOW
    "conformer-generation": (
        "Predict the most stable structure when given only chemical composition "
        "or system. Strategies range from evolutionary searches to "
        "substituition of known materials."
    ),
    "docking": (
        "Analyze ligand-protein binding affinity and preferred orientation. "
        "Simulations can also be ran accross larger datasets "
        "to evaluate probable mode(s) of action."
    ),
    "clustering": (
        "Group a list of molecules or crystals based on chemical similarity. "
        "These workflows can also be used to generate diverse subsets of compounds "
        "for further analysis."
    ),
}

DEFAULT_DESCRIPTION = "A custom workflow type, built internally. (no description given)"

TYPE_DESCRIPTIONS = {
    t: (
        settings.website.workflows.type_descriptions.get(t)
        if t in settings.website.workflows.type_descriptions
        else DEFAULT_TYPE_DESCRIPTIONS.get(t, DEFAULT_DESCRIPTION)
    )
    for t in settings.website.workflows.types_to_display
}


def all_workflow_types(request):
    context = {
        "workflows_metadata": TYPE_DESCRIPTIONS,
        "breadcrumbs": ["Workflows"],
    }
    template = "workflows/all_workflow_types.html"
    return render(request, template, context)


def workflows_of_given_type(request, workflow_type):
    apps = get_apps_by_type(workflow_type)

    # pull the information together for each individual flow and organize by
    # workflow app.
    workflow_dict = {}
    for app in apps:
        workflow_names = get_workflow_names_by_type(
            workflow_type,
            app,
            remove_no_database_flows=False,
        )
        workflow_dict[app] = [get_workflow(n) for n in workflow_names]

    context = {
        "workflow_type": workflow_type,
        "workflow_type_description": TYPE_DESCRIPTIONS[workflow_type],
        "workflow_dict": workflow_dict,
        "page_title": "Workflow Type",
        "breadcrumbs": ["Workflows", workflow_type],
    }
    template = "workflows/workflows_of_given_type.html"
    return render(request, template, context)


def workflows_of_given_type_and_app(request, workflow_type, workflow_app):
    workflow_names = get_workflow_names_by_type(
        workflow_type,
        workflow_app,
        remove_no_database_flows=False,
    )
    workflows = [get_workflow(n) for n in workflow_names]

    context = {
        "workflows": workflows,
        "page_title": f"{workflow_type}.{workflow_app}",
        "breadcrumbs": ["Workflows", workflow_type, workflow_app],
    }
    template = "workflows/workflows_of_given_type_and_app.html"
    return render(request, template, context)


def workflow_detail(request, workflow_type, workflow_app, workflow_preset):

    workflow_name = f"{workflow_type}.{workflow_app}.{workflow_preset}"
    workflow = get_workflow(workflow_name)

    # TODO: grab some metadata about this calc. For example...
    # ncalculations = workflow.all_results.objects.count()
    # nflows_submitted = workflow.nflows_submitted
    # workflow.database_table

    context = {
        "workflow": workflow,
        "page_title": workflow_name,
        "breadcrumbs": ["Workflows", workflow_type, workflow_app, workflow_preset],
    }
    template = "workflows/workflow_detail.html"
    return render(request, template, context)


@login_required
def workflow_submit(
    request,
    workflow_type: str,
    workflow_app: str,
    workflow_preset: str,
):
    name_full = f"{workflow_type}.{workflow_app}.{workflow_preset}"
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
