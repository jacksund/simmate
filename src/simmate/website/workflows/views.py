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


def home(request):
    context = {
        "breadcrumbs": ["Workflows"],
    }
    template = "workflows/home.html"
    return render(request, template, context)


def all_workflow_types(request):
    context = {
        "workflows_metadata": TYPE_DESCRIPTIONS,
        "breadcrumbs": ["Workflows"],
    }
    template = "workflows/all_workflow_types.html"
    return render(request, template, context)


def workflow_detail(request, workflow_name):

    # workflow_name = f"{workflow_type}.{workflow_app}.{workflow_preset}"
    workflow = get_workflow(workflow_name)

    # TODO: grab some metadata about this calc. For example...
    # ncalculations = workflow.all_results.objects.count()
    # nflows_submitted = workflow.nflows_submitted
    # workflow.database_table

    context = {
        "workflow": workflow,
        "page_title": workflow_name,
        "breadcrumbs": ["Workflows", workflow_name],
    }
    template = "workflows/workflow_detail.html"
    return render(request, template, context)
