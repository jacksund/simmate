# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .worker import SimmateWorker
from .work_item import WorkItem


class SimmateWorkerTable(DynamicTableForm):
    table = SimmateWorker
    html_display_name = "Workers"
    html_description_short = (
        "Computational agents responsible for executing submitted tasks. "
        "This table monitors the health, resource usage, and active jobs "
        "for each worker in the cluster."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/workers/table.html",
    }


class WorkItemTable(DynamicTableForm):
    table = WorkItem
    html_display_name = "Work Items"
    html_description_short = (
        "Specific tasks or jobs that have been submitted to a queue for "
        "execution by workers. This table tracks the lifecycle of a "
        "calculation, including its parameters, status, and any errors "
        "encountered."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/work_items/table.html",
    }
