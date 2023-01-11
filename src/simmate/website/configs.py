# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreComponentsConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.core_components"


class WorkflowsConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.workflows"


class WorkflowEngineConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.workflow_engine"


class ThirdPartyConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.third_parties"


class TestAppConfig(AppConfig):

    # use the full import path for this app b/c it's within a package
    name = "simmate.website.test_app"
