# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path(
        route="",
        view=views.home,
        name="home",
    ),
    path(
        route="component/<component_id>/",
        view=views.component_call,
        name="component",
    ),
    path(
        route="component/<component_id>/<method_name>/",
        view=views.component_call,
        name="component_method",
    ),
]
