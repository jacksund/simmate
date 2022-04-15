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
    # This two views are for the Spacegroup table. "symmetry" lists all of the
    # 230 spacegroups while "spacegroup" is for a single one.
    path(
        route="symmetry/",
        view=views.SymmetryViewSet.list_view,
        name="symmetry",
    ),
    path(
        route="symmetry/<pk>/",
        view=views.SymmetryViewSet.retrieve_view,
        name="spacegroup",
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
