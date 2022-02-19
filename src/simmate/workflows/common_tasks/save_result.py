# -*- coding: utf-8 -*-

import prefect
from prefect import Task


class SaveOutputTask(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(self, output):

        # split our results and corrections (which are given as a dict) into
        # separate variables
        vasprun = output["result"]
        corrections = output["corrections"]
        directory = output["directory"]

        # load the calculation entry for this workflow run. This should already
        # exist thanks to the load_input_and_register task.
        calculation = self.calculation_table.from_prefect_id(
            prefect.context.flow_run_id,
        )

        # now update the calculation entry with our results
        calculation.update_from_vasp_run(vasprun, corrections, directory)

        return calculation.id
