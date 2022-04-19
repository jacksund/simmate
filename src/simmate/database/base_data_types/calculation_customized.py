# -*- coding: utf-8 -*-

from pymatgen.io.vasp.outputs import Vasprun
from simmate.database.base_data_types import table_column, Calculation


class CustomizedCalculation(Calculation):
    """
    A customized calculation is when the corresponding workflow has been
    fundamentally changed -- meaning critical settings for the workflow were
    updated. For example, we may want to run a workflow that uses different
    convergence critria or even add a correction setting (e.g. a dispersion
    correction). Simmate aims to store this data separately from the main
    workflow's result table, so this table holds the results from altered runs.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    workflow_base = table_column.CharField(blank=True, null=True, max_length=75)
    """
    The name of the workflow that is updated. (e.g. "relaxation/matproj")
    """

    input_parameters = table_column.JSONField(blank=True, null=True)
    """
    The attributes updated on the `base_workflow` before the flow was ran
    """

    updated_settings = table_column.JSONField(blank=True, null=True)
    """
    The attributes updated on the `base_workflow` before the flow was ran
    """

    data = table_column.JSONField(blank=True, null=True)
    """
    The final data from the calculation. Because there are a variety of possible
    results, all data is stored as JSON.
    """

    def update_from_vasp_run(
        self,
        vasprun: Vasprun,
        corrections: list,
        directory: str,
    ):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.

        # rather than cherry-pick data, we just save everything as a dictionary
        self.data = vasprun.as_dict()

        # lastly, we also want to save the corrections made and directory it ran in
        self.corrections = corrections
        self.directory = directory

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()
