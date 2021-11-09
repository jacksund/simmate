# -*- coding: utf-8 -*-

import prefect
from prefect import Task


class SaveResultTask(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(self, result):

        # split our results and corrections (which are given as a tuple) into
        # separate variables
        vasprun, corrections = result

        # load/create the calculation for this workflow run
        calculation = self.calculation_table.from_prefect_id(
            prefect.context.flow_run_id,
            structure=vasprun.initial_structure,
            # BUG: what if the initial structure changed? An example of this happening
            # is with a relaxation where a correction was applied and the calc
            # was not fully restarted. This issue also will not matter when
            # workflows are ran through cloud -- as the structure is already
            # saved and won't be overwritten here.
        )

        # now update the calculation entry with our results
        calculation.update_from_vasp_run(vasprun, corrections)

        return calculation.id
