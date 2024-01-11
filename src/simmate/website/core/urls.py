# -*- coding: utf-8 -*-

from django.contrib import admin
from django.urls import include, path

from simmate.configuration import settings
from simmate.utilities import get_app_submodule
from simmate.website.core import views


def get_app_urls():
    # First let's find our custom simmate apps that supply a 'urls' module. We
    # want to automatically make these avaialable in the web UI.

    extra_url_paths = []

    for app_name in settings.apps:
        urls_path = get_app_submodule(app_name, "urls")
        if urls_path:
            simple_name = urls_path.split(".")[-2]
            new_path = path(
                route=f"apps/{simple_name}/",
                # set the namespace so that we can easily look up app urls
                #   https://stackoverflow.com/questions/48608894
                view=include((urls_path, simple_name), namespace=simple_name),
                name=simple_name,
            )
            extra_url_paths.append(new_path)

    return extra_url_paths


def get_disabled_urls():
    """
    Collects any pages that should be disabled
    """
    disabled_url_paths = []

    # We want to turn off the new account signup form if we require all users
    # to sign in using their allauth (e.g. Microsoft login)
    if settings.website.require_login_internal:
        new_path = path(route="accounts/signup/", view=views.permission_denied)
        disabled_url_paths.append(new_path)

    return disabled_url_paths


urlpatterns = [
    #
    # This is the path to the homepage (just simmate.org)
    path(route="", view=views.home, name="home"),
    #
    # Disabled urls (such as the account signup form), must come first. The only
    # page that can't be disabled is the home page.
    *get_disabled_urls(),
    #
    # This is the built-in admin site that django provides
    path(route="admin/", view=admin.site.urls, name="admin"),
    #
    # This is the profile system with login/logout.
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
        route="data/",
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
    # Django-unicorn urls
    path("unicorn/", include("django_unicorn.urls")),
    #
    # Django-contrib-comments urls
    path("comments/", include("django_comments.urls")),
    #
    # Custom Simmate apps (if present)
    path(route="apps/", view=views.apps, name="apps"),
    *get_app_urls(),
]
