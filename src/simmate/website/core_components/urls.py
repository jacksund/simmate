# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.core_components import views

urlpatterns = [
    path(
        route="",
        view=views.structure_viewer,
        name="structure_viewer",
    ),
    path(
        route="test/",
        view=views.test_viewer,
        name="test_viewer",
    ),
]
