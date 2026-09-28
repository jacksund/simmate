# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    context = {
        "page_title": "Dev Tools",
        "breadcrumbs": ["Apps", "Dev Tools"],
    }
    return render(request, "dev_tools/home.html", context)
