# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from prefect.backend.flow_run import FlowView

from simmate.database.local_calculations import (
    MITRelaxation,
    # MITIonicStep,
)
from simmate.website.local_calculations.forms import MITRelaxationForm
from simmate.workflow_engine import WorkflowTask


@login_required
def all_local_calculations(request):

    # now let's put the data and template together to send the user
    context = {"active_tab_id": "workflows"}
    template = "local_calculations/all.html"
    return render(request, template, context)


@login_required
def relaxations(request):

    # In order to make links to the monitoring pages for each of these, we need
    # to grab the prefect id
    # BUG: If no flow exists, a ValueError is raised. I may want to account for
    # this when the user doesn't have Prefect set up.
    mit_flow_id = FlowView.from_flow_name("MIT Relaxation").flow_id

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "workflows",
        "mit_flow_id": mit_flow_id,
    }
    template = "local_calculations/relaxations.html"
    return render(request, template, context)


@login_required
def mit_about(request):

    # In order to make links to the monitoring pages for each of these, we need
    # to grab the prefect id
    # BUG: If no flow exists, a ValueError is raised. I may want to account for
    # this when the user doesn't have Prefect set up.
    mit_flow_id = FlowView.from_flow_name("MIT Relaxation").flow_id

    # TODO: grab some metadata about this calc. For example...
    # ncalculations = MITRelaxation.objects.count()

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "workflows",
        "mit_flow_id": mit_flow_id,
    }
    template = "local_calculations/mit/about.html"
    return render(request, template, context)


@login_required
def mit_submit(request):

    if request.method == "POST":
        submission_form = MITRelaxationForm(request.POST, request.FILES)
        if submission_form.is_valid():
            # grab the structure (as a pymatgen object) and all other inputs
            structure = submission_form.cleaned_data["structure_file"]
            labels = submission_form.cleaned_data["labels"]
            vasp_command = submission_form.cleaned_data["vasp_command"]

            # We can now submit the workflow for the structure.
            flowtask = WorkflowTask(workflow_name="MIT Relaxation")
            flow_run_id = flowtask.run(
                structure=structure,
                vasp_command=vasp_command,
                labels=labels,
                wait_for_run=False,
            )

            return redirect(f"https://cloud.prefect.io/simmate/flow-run/{flow_run_id}")
    else:
        submission_form = MITRelaxationForm()

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "workflows",
        "submission_form": submission_form,
    }
    template = "local_calculations/mit/submit.html"
    return render(request, template, context)


@login_required
def mit_all(request):

    # Grab the most recent 50 MIT relaxations that have been registered/ran
    calculations = MITRelaxation.objects.order_by("created_at").reverse().all()[:50]

    # We also want to count how many total calculations there are.
    ncalculations_possible = MITRelaxation.objects.count()

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "workflows",
        "calculations": calculations,
        "ncalculations_possible": ncalculations_possible,
    }
    template = "local_calculations/mit/all.html"
    return render(request, template, context)


@login_required
def mit_single(request, mitrelax_id):

    # Grab the most recent 50 MIT relaxations that have been registered/ran
    calculation = MITRelaxation.objects.get(id=mitrelax_id)

    # Make the convergence figure and convert it to an html div
    figure_convergence = calculation.get_convergence_plot()
    figure_convergence_html = figure_convergence.to_html(
        full_html=False, include_plotlyjs=False
    )

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "workflows",
        "calculation": calculation,
        "figure_convergence_html": figure_convergence_html,
    }
    template = "local_calculations/mit/single.html"
    return render(request, template, context)
