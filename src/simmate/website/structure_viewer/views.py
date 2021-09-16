# -*- coding: utf-8 -*-

from django.shortcuts import render


def structure_viewer(request):
    context = {}
    template = "structure_viewer/main.html"
    return render(request, template, context)
