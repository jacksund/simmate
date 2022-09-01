# -*- coding: utf-8 -*-

"""
WARNING: This module is still at the planning stage and the code below serve as
placeholder notes.

In the future, it will be a table that helps link together results from
multi-stage workflows.
"""

from simmate.database.base_data_types import Calculation  # , table_column


class NestedCalculation(Calculation):
    """
    A nested calculation is extremely similar to a calculation table, except here
    the linked workflow is a NestedWorkflow -- meaning it is made of multiple
    smaller workflows. For example, we may want to run a workflow that runs a
    series of relaxations. Or maybe a relaxation, then energy, then band-strucuture
    calculation. This table is for keeping track of workflows ran in series like
    this.

    Typically, you'll use the `create_subclass_from_calcs` method to create a
    subclass of this table, which handles making all the relationships for you.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    # TODO:
    # child_database_tables = [...]

    # TODO:
    # should this be a list of all modifications? It could maybe be used to
    # carry fixes (such as smearing) accross different calcs.
    # Or maybe a method that just lists the corrections of each subcalc?
    corrections = None
    # For now I delete this column. This line removes the field.

    # def update_calculation(self):
    #     """
    #     This is an experimental method that iterates through child workflow tables
    #     and links the results to the NestedCalculation
    #     """
    #     # BUG: This assumes we ran all calculations within the same directory,
    #     # which isn't true in all cases.
    #     for child_calc_table in self.child_database_tables:
    #         if child_calc_table.objects.filter(directory=self.directory).exists():
    #             child_calc = child_calc_table.objects.get(directory=self.directory)
    #             setattr(self, child_calc._meta.model_name, child_calc)
    #     self.save()
