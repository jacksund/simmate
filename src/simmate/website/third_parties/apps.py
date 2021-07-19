from django.apps import AppConfig


class ThirdPartyConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.third_parties"
