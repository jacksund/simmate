# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "simmate.website.core"


class ComputeManagementConfig(AppConfig):
    name = "simmate.website.compute_management"
    url_prefix = "compute"  # the worker REST API is served under apps/compute/
    verbose_name = "Compute Management"
    description_short = (
        "A dashboard for monitoring cluster workers, queues, and compute resources"
    )
    app_card_template = "compute_management/app_card.html"


class DataExplorerConfig(AppConfig):
    name = "simmate.website.data_explorer"


class HtmxConfig(AppConfig):
    name = "simmate.website.htmx"


class WorkflowExplorerConfig(AppConfig):
    name = "simmate.website.workflow_explorer"


class TestAppConfig(AppConfig):
    name = "simmate.website.test_app"
