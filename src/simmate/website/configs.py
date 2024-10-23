# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreComponentsConfig(AppConfig):
    name = "simmate.website.core_components"


class DataExplorerConfig(AppConfig):
    name = "simmate.website.data_explorer"


class UserTrackingConfig(AppConfig):
    name = "simmate.website.user_tracking"


class WorkflowsConfig(AppConfig):
    name = "simmate.website.workflows"


class WorkflowEngineConfig(AppConfig):
    name = "simmate.website.engine"


class TestAppConfig(AppConfig):
    name = "simmate.website.test_app"
