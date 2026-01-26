# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.workflows.utilities import get_workflow


def home(request):
    context = {
        "breadcrumbs": ["Workflows"],
    }
    template = "workflows/home.html"
    return render(request, template, context)


def workflow_detail(request, workflow_name):

    workflow = get_workflow(workflow_name)

    # TODO: grab some metadata about this calc. For example...
    # ncalculations = workflow.all_results.objects.count()

    context = {
        "workflow": workflow,
        "page_title": workflow_name,
        "breadcrumbs": ["Workflows", workflow_name],
    }
    template = "workflows/workflow_detail.html"
    return render(request, template, context)
