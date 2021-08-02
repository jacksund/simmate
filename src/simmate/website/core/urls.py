# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import include, path

from simmate.website.core import views

urlpatterns = [
    #
    # This is the path to the homepage (just simmate.org)
    path(
        route="",
        view=views.home,
        name="home",
    ),
    #
    # This is the built-in admin site that django provides
    path(
        route="admin/",
        view=admin.site.urls,
        name="admin",
    ),
    #
    # This is profile system with login/logout
    path(
        route="accounts/",
        view=include("simmate.website.accounts.urls"),
        name="accounts",
    ),
    #
    #
    path(
        route="third-parties/",
        view=include("simmate.website.third_parties.urls"),
        name="third_parties",
    ),
    #
    #
    # This maps to our REST api endpoints
    path(
        route="rest-api/",
        view=include("simmate.website.rest_api.urls"),
        name="rest_api",
    ),
]
