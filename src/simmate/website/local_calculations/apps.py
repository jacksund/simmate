from django.apps import AppConfig


class LocalCalculationsConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.local_calculations"
