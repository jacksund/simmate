# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Project Management dashboard. All metrics are rendered (and
    auto-refreshed) by the `ProjectDashboardComponent`.
    """
    context = {
        "page_title": "Project Management",
        "breadcrumbs": ["Apps", "Project Management"],
    }
    return render(request, "project_management/home.html", context)
