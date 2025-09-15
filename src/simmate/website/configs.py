# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreComponentsConfig(AppConfig):
    name = "simmate.website.core_components"


class DataExplorerConfig(AppConfig):
    name = "simmate.website.data_explorer"


class HtmxConfig(AppConfig):
    name = "simmate.website.htmx"


class UnicornConfig(AppConfig):
    name = "simmate.website.unicorn"


class WorkflowsConfig(AppConfig):
    name = "simmate.website.workflows"


class TestAppConfig(AppConfig):
    name = "simmate.website.test_app"
