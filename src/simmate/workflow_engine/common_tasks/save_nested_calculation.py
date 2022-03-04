# -*- coding: utf-8 -*-

# NOTE: This task isn't used at all yet because my update_calculation method
# of NestedCalculation is broken.

import prefect
from prefect import Task


class SaveNestedCalculationTask(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(self):

        # first grab the calculation entry
        calc = self.calculation_table.from_prefect_id(prefect.context.flow_run_id)

        # now update the calculation
        calc.update_calculation()
