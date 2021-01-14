# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    context = {}
    template = "website/home.html"  # !!! Doesn't exist at the moment
    return render(request, template, context)
