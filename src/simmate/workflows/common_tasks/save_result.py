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

        # BUG-FIX: see vasptask base for more
        if isinstance(vasprun, dict):
            vasprun = vasprun["vasprun"]

        # load/create the calculation for this workflow run
        calculation = self.calculation_table.from_prefect_id(
            prefect.context.flow_run_id,
            # We pass the initial structure in can the calculation wasn't created
            # yet (and creation requires the structure)
            structure=vasprun.initial_structure,
            # BUG: what if the initial structure changed? An example of this happening
            # is with a relaxation where a correction was applied and the calc
            # was not fully restarted. This issue also will not matter when
            # workflows are ran through cloud -- as the structure is already
            # saved and won't be overwritten here.
        )

        # now update the calculation entry with our results
        calculation.update_from_vasp_run(vasprun, corrections, directory)

        return calculation.id
