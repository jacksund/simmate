# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from ..core import table_column
from .calculation import Calculation
from .forces import Forces
from .structure import Structure
from .thermodynamics import Thermodynamics


class StagedWorkflow(Calculation):
    class Meta:
        abstract = True

    subworkflow_runs = table_column.JSONField(blank=True, null=True, default=list)

    @property
    def subworkflows(self):
        from simmate.workflows.utils import get_workflow

        workflow_class = get_workflow(self.workflow_name)
        subworkflow_names = workflow_class.subworkflow_names

        return [get_workflow(name) for name in subworkflow_names]

    @property
    def database_tables(self):
        subworkflows = self.subworkflows
        return [subworkflow.database_table for subworkflow in subworkflows]

    @property
    def subworkflow_results(self):
        results = []
        if not self.subworkflow_runs:
            return results
        
        if len(self.subworkflow_runs) != len(self.database_tables):
            logging.warning(
                "This staged workflow did not complete. Some results may be missing."
            )
            # We don't return early here because we might still want the results of the subworkflows that DID complete.
            
        for run_dict, table in zip(self.subworkflow_runs, self.database_tables):
            sub_id = run_dict.get("id")
            if sub_id and table.objects.filter(id=sub_id).exists():
                results.append(table.objects.get(id=sub_id))
            else:
                results.append(None)
        return results


