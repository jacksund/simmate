# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.workflow_explorer import views

urlpatterns = [
    path(
        route="",
        view=views.home,
        name="home",
    ),
    path(
        route="<workflow_name>/",
        view=views.workflow_detail,
        name="workflow_detail",
    ),
]
