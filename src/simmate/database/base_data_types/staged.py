# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Calculation, Structure , table_column
from pathlib import Path


class StagedCalculation(Structure, Calculation):
    """
    Staged calculations are calculations that involve running multiple workflows
    stringed together. For example, we may want to run several relaxation
    calculations of increasing quality. This table connects these staged
    calculations by storing the subworkflow names and ids. It provides convenience
    methods to get the results of these subworkflows.
    """

    class Meta:
        app_label = "workflows"

    
    subworkflow_names = table_column.JSONField(blank=True, null=True)
    """
    A list of subworkflow string names
    """
    
    subworkflow_ids = table_column.JSONField(blank=True, null=True)
    """
    A list of the id pointing to each workflow result's location in their
    respective databases
    """
    
    copied_files = table_column.JSONField(blank=True, null=True)
    """
    A list of the files that were copied between calculations
    """
    # TODO:
    # should this be a list of all modifications? It could maybe be used to
    # carry fixes (such as smearing) accross different calcs.
    # Or maybe a method that just lists the corrections of each subcalc?
    corrections = None
    # For now I delete this column. This line removes the field.
    # TODO:
    # Should this also include the initial and final structure? This would require
    # that the involved calculations are structure calculations and remove some
    # versatility, but it would be convenient and is likely the main way this
    # table will be used.
    
    # !!! There may be a more direct way to store this information using
    # one-to-one keys or other. Ideally this would directly connect items in
    # this table to the subworkflow tables.
    
    @property
    def subworkflows(self):
        from simmate.workflows.utilities import get_workflow
        subworkflow_names = self.subworkflow_names
        return [get_workflow(name) for name in subworkflow_names]
        
    @property
    def database_tables(self):
        subworkflows = self.subworkflows
        return [subworkflow.database_table for subworkflow in subworkflows]
    
    @property
    def subworkflow_results(self):
        results = []
        for sub_id, table in zip(self.subworkflow_ids, self.database_tables):
            if table.objects.filter(id=sub_id).exists():
                results.append(table.objects.get(id=sub_id))
            else:
                results.append(None)
        return results

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)

    def update_from_directory(self, directory: Path):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
            
            
            
