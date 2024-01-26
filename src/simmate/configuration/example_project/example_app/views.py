# -*- coding: utf-8 -*-

"""
Simmate will build interfaces for your workflows and tables. However, if you
want to add extra webpages for your app, then you'll need to build "views" in 
this file out. 

If you ever venture to this level, we STRONGLY recommend you go through the
django tutorials first: https://docs.djangoproject.com/en/3.2/
"""

from django.shortcuts import render


# Simple views (like a homepage) are made following django's normal format
def example_view(request):
    context = {}
    template = "path/to/my/template.html"
    return render(request, template, context)


# NOTE: You can delete this file if you decide not to use it.
