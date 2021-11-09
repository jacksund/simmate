# -*- coding: utf-8 -*-

import prefect
from prefect import Task


class SaveResultsTask(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(self, result_and_corrections):

        # split our results and corrections (which are given as a tuple) into
        # separate variables
        vasprun, corrections = result_and_corrections

        # load/create the calculation for this workflow run
        calculation = self.calculation_table.from_prefect_id(
            prefect.context.flow_run_id
        )

        # now update the calculation entry with our results
        calculation.update_from_vasp_run(vasprun, corrections)

        return calculation.id
