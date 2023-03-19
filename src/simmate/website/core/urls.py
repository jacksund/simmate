# -*- coding: utf-8 -*-

import importlib

from django.contrib import admin
from django.urls import include, path

from simmate.configuration.django.settings import SIMMATE_APPS
from simmate.website.core import views


def get_app_urls():
    # First let's find our custom simmate apps that supply a 'urls' module. We
    # want to automatically make these avaialable in the web UI.

    extra_url_paths = []

    for app_name in SIMMATE_APPS:
        # This section of code is copied from...
        #   simmate.workflows.utilities.get_all_workflows
        # Consider making another util.
        config_modulename = ".".join(app_name.split(".")[:-1])
        config_name = app_name.split(".")[-1]
        config_module = importlib.import_module(config_modulename)
        config = getattr(config_module, config_name)
        app_path = config.name
        simple_name = app_path.split(".")[-1]

        # check if there is a urls module in the app
        #   stackoverflow.com/questions/14050281
        urls_found = importlib.util.find_spec(f"{app_path}.urls") is not None

        if urls_found:
            new_path = path(
                route=f"apps/{simple_name}/",
                # set the namespace so that we can easily look up app urls
                #   https://stackoverflow.com/questions/48608894
                view=include((f"{app_path}.urls", simple_name), namespace=simple_name),
                name=simple_name,
            )
            extra_url_paths.append(new_path)

    return extra_url_paths


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
            ("simmate.website.data_explorer.urls", "simmate.website.data_explorer"),
            namespace="data_explorer",
        ),
        name="data_explorer",
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
    #
    # Custom Simmate apps (if present)
    path(route="apps/", view=views.apps, name="apps"),
    *get_app_urls(),
]
