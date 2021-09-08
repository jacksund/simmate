# -*- coding: utf-8 -*-

import plotly.express as plotlyexpress
from django_pandas.io import read_frame

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from simmate.database.local_calculations.relaxation.mit import (
    MITRelaxation,
    MITRelaxationStructure,
)


@login_required
def all_local_calculations(request):

    # now let's put the data and template together to send the user
    context = {"active_tab_id": "workflows"}
    template = "local_calculations/all.html"
    return render(request, template, context)


@login_required
def relaxations(request):

    # now let's put the data and template together to send the user
    context = {"active_tab_id": "workflows"}
    template = "local_calculations/relaxations.html"
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
    template = "local_calculations/mit_all.html"
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
    template = "local_calculations/mit_single.html"
    return render(request, template, context)
