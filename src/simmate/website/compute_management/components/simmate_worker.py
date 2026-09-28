# -*- coding: utf-8 -*-

from simmate.compute import SimmateWorker
from simmate.website.data_explorer.components import TableComponent


class SimmateWorkerComponent(TableComponent):
    table = SimmateWorker
    display_name = "Workers"
    description_short = (
        "Computational agents responsible for executing submitted tasks. "
        "This table monitors the health, resource usage, and active jobs "
        "for each worker in the cluster."
    )
    template_names = {
        "entries": "compute_management/workers/table.html",
    }
