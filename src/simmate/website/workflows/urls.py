# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.workflows import views

urlpatterns = [
    path(
        route="",
        view=views.home,
        name="workflows",
    ),
    path(
        route="<workflow_name>/",
        view=views.workflow_detail,
        name="workflow_detail",
    ),
]
