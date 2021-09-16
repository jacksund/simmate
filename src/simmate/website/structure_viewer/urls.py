# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.structure_viewer import views

urlpatterns = [
    path(
        route="",
        view=views.structure_viewer,
        name="test",
    ),
]
