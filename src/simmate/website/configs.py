# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreComponentsConfig(AppConfig):
    name = "simmate.website.core_components"


class WorkflowsConfig(AppConfig):
    name = "simmate.website.workflows"


class WorkflowEngineConfig(AppConfig):
    name = "simmate.website.workflow_engine"


class ThirdPartyConfig(AppConfig):
    name = "simmate.website.third_parties"


class TestAppConfig(AppConfig):
    name = "simmate.website.test_app"
