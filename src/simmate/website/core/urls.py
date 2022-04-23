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
        view=include("allauth.urls"),
        name="accounts",
    ),
    # On login success, you will be pointed to /accounts/profile by default.
    # If you want to change this defualt, then set LOGIN_REDIRECT_URL in
    # the settings.py file
    path(route="accounts/profile/", view=views.profile, name="profile"),
    # When you sign out, you are sent to LOGOUT_REDIRECT_URL (set in settings.py)
    path(route="accounts/loginstatus/", view=views.loginstatus, name="loginstatus"),
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
    #
    # And extra one-page views
    path(route="extras/", view=views.extras, name="extras"),
    path(route="contact/", view=views.contact, name="contact"),
    path(route="about/", view=views.about, name="about"),
]
