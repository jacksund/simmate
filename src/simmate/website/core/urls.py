# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import include, path

from simmate.website.core import views


urlpatterns = [
    #
    # This is the path to the homepage (just simmate.org)
    path(route="", view=views.home, name="home"),
    #
    # This is the built-in admin site that django provides
    path(route="admin/", view=admin.site.urls, name="admin"),
    #
    # This is profile system with login/logout
    path(
        route="accounts/",
        view=include("simmate.website.accounts.urls"),
        name="accounts",
    ),
    #
    #
    path(route="extras/", view=views.extras, name="extras"),
    #
    #
    path(
        route="third-parties/",
        view=include(
            ("simmate.website.third_parties.urls", "simmate.website.third_parties"),
            namespace="third_parties",
        ),
        name="third_parties",
    ),
    #
    #
    # All local calculations are stored at this endpoint
    path(
        route="workflows/",
        view=include("simmate.website.workflows.urls"),
        name="workflows",
    ),
    #
    # This app includes core functionality, such as views for crystal structures
    # in a 3D viewport.
    path(
        route="core-components/",
        view=include(
            (
                "simmate.website.core_components.urls",
                "simmate.website.core_components",
            ),
            namespace="core_components",
        ),
        name="core_components",
    ),
]
