# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "simmate.website.core"


class DataExplorerConfig(AppConfig):
    name = "simmate.website.data_explorer"


class HtmxConfig(AppConfig):
    name = "simmate.website.htmx"


class WorkflowsConfig(AppConfig):
    name = "simmate.website.workflows"


class TestAppConfig(AppConfig):
    name = "simmate.website.test_app"
