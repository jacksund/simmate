# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.core_components import views

urlpatterns = [
    # This view is meant to be used as an iFrame for viewing 3D crystal structures
    path(
        route="structure-viewer/",
        view=views.structure_viewer,
        name="structure_viewer",
    ),
    #
    # This view is strictly for testing different components and making sure
    # they are working.
    path(
        route="test/",
        view=views.test_viewer,
        name="test_viewer",
    ),
]
