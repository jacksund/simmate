# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    context = {"active_tab_id": "home"}
    template = "core/home.html"
    return render(request, template, context)
