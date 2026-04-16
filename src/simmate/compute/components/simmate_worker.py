# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..worker import SimmateWorker


class SimmateWorkerComponent(TableComponent):
    table = SimmateWorker
    display_name = "Workers"
    description_short = (
        "Computational agents responsible for executing submitted tasks. "
        "This table monitors the health, resource usage, and active jobs "
        "for each worker in the cluster."
    )
    template_names = {
        "entries": "workflow_explorer/workers/table.html",
    }
