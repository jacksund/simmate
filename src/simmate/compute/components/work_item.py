# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..work_item import WorkItem


class WorkItemComponent(TableComponent):
    table = WorkItem
    display_name = "Work Items"
    description_short = (
        "Specific tasks or jobs that have been submitted to a queue for "
        "execution by workers. This table tracks the lifecycle of a "
        "calculation, including its parameters, status, and any errors "
        "encountered."
    )
    template_names = {
        "entries": "workflow_explorer/work_items/table.html",
    }
