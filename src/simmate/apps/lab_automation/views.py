# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    context = {
        "page_title": "Lab Automation",
        "breadcrumbs": ["Apps", "Lab Automation"],
    }
    return render(request, "lab_automation/home.html", context)
