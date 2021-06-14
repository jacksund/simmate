# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    context = {}
    template = "core/home.html"
    return render(request, template, context)
