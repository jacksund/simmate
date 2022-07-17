# -*- coding: utf-8 -*-

"""
Want to make a website interface for your app? Then you'll need to fill this file
out! If you ever venture to this level, we strongly recommend you go through the
django tutorials first: https://docs.djangoproject.com/en/3.2/

COMING SOON: Simmate will automatically build out views for a workflow based
on what your database table looks like. Let us know if you are waiting on this
feature, so we can prioritize it!
"""

from django.shortcuts import render

from simmate.website.core_components.base_api_view import SimmateAPIViewSet

from .models import ExampleRelaxationTable

# Simple views (like a homepage) are made following django's normal format
def example_view(request):
    context = {}
    template = "path/to/my/template.html"
    return render(request, template, context)


# Advanced views that automatically generate a user interface and API for you
# use a class from Simmate!
class ExampleRelaxationViewSet(SimmateAPIViewSet):
    table = ExampleRelaxationTable
    # NOTE: default templates are still under development. For now, you can
    # reference our own templates to get started.
    template_list = "path/to/my/template1.html"
    template_retrieve = "path/to/my/template2.html"
