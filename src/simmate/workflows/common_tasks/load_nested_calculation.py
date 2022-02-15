# -*- coding: utf-8 -*-

import prefect
from prefect import Task

from simmate.utilities import get_directory


class LoadNestedCalculationTask(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(self, directory):

        # first grab the calculation entry
        calc = self.calculation_table.from_prefect_id(prefect.context.flow_run_id)

        # even though S3Task creates a directory when passed None, it is useful
        # to make it here first because some workflows require the folder name between
        # each calculation (see workflows.relaxation.staged for an example). We therefore
        # make the directory upfront!
        new_directory = get_directory(directory)

        # set the directory for the calculation
        calc.directory = get_directory(new_directory)
        calc.save()

        return new_directory
