from django.apps import AppConfig


class AccountsConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.accounts"
