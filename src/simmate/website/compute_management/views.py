# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Compute dashboard. All metrics are rendered (and auto-refreshed) by the
    `ComputeDashboardComponent`.
    """
    context = {
        "page_title": "Compute Dashboard",
        "breadcrumbs": ["Apps", "Compute"],
    }
    return render(request, "compute_management/home.html", context)
