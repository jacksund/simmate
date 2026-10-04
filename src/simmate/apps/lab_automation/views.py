# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Lab Automation dashboard. All panels are rendered by the
    `LabDashboardComponent`, and each sensor card refreshes itself.
    """
    context = {
        "page_title": "Lab Automation",
        "breadcrumbs": ["Apps", "Lab Automation"],
    }
    return render(request, "lab_automation/home.html", context)
