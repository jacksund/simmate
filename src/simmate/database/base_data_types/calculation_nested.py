# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Calculation

from typing import List


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

    @classmethod
    def create_subclass_from_calcs(
        cls,
        name: str,
        child_database_tables: List[Calculation],
        module: str,
        **extra_columns,
    ):
        """
        Dynamically creates a subclass of NestedCalculation -- and handles linking
        together all child calculation tables.

        `simmate.calculators.vasp.database.relaxation` shows an example of creating
        a table from this class:

        ``` python
        StagedRelaxation = NestedCalculation.create_subclass_from_calcs(
            "StagedRelaxation",
            [
                Quality00Relaxation,
                Quality01Relaxation,
                Quality02Relaxation,
                Quality03Relaxation,
                Quality04Relaxation,
            ],
            module=__name__,
        )
        ```

        To add custom columns, you can do the following:

        ``` python
        from simmate.database.base_data_types import table_column

        StagedRelaxation = NestedCalculation.create_subclass_from_calcs(
            ... # everything is the same as above
            custom_column_01=table_column.FloatField()
        )
        ```

        #### Parameters

        - `name` :
            Name of the subclass that is output.
        - `child_database_tables` :
            list of database tables for the nested workflows. This table links
            these sub-tables together so results can be viewed from each step.
        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.
        **extra_columns : TYPE
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        #### Returns

        NewClass :
            A subclass of NestedCalculation.

        """

        # BUG: I assume a workflow won't point to the save calculation table
        # more than once... What's a scenario where this isn't true?
        # I can only think of multi-structure workflows (like EvolutionarySearch)
        # which I don't give their own table for now.
        new_columns = {}
        for child_calc in child_database_tables:
            new_column = table_column.OneToOneField(
                child_calc,
                on_delete=table_column.CASCADE,
                # related_name=...,
                blank=True,
                null=True,
            )
            new_columns[f"{child_calc._meta.model_name}"] = new_column

        # Now put all the fields together to make the new class
        NewClass = cls.create_subclass(
            name,
            **new_columns,
            **extra_columns,
            # also have child calcs list as an attribute
            child_database_tables=child_database_tables,
            module=module,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewClass

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
