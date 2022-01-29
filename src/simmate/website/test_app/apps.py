from django.apps import AppConfig


class TestAppConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.test_app"
