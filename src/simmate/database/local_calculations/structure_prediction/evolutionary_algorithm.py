# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, DatabaseTable

from simmate.database.local_calculations.relaxation.mit import (
    # MITRelaxation,
    MITRelaxationStructure,
)


class EvolutionarySearch(DatabaseTable):

    # consider formula_full or chemical_system by making a composition-based mixin
    composition = table_column.CharField(max_length=50)

    # Import path for the workflow
    # !!! Or should this be JSON? Or even an extra table with fields?
    workflow = table_column.CharField(max_length=200)
    individuals_datatable = table_column.CharField(max_length=200)

    # Import path that grabs the fitness value
    # I assume energy for now
    # fitness_function = table_column.CharField(max_length=200)

    max_structures = table_column.IntegerField()
    limit_best_survival = table_column.IntegerField()

    # relationships
    # sources / individuals
    # stop_conditions

    # get_stats:
    #   Total structure counts
    #   makeup of random, heredity, mutation, seeds, COPEX

    class Meta:
        app_label = "local_calculations"


class StructureSource(DatabaseTable):

    # is_steadystate / is_singleshot

    name = table_column.CharField(max_length=50)

    settings = table_column.JSONField(default=None, blank=True, null=True)

    is_running = table_column.BooleanField()

    # timestamping for when this was added to the database
    started_at = table_column.DateTimeField(auto_now_add=True)
    stopped_at = table_column.DateTimeField(blank=True, null=True)

    # structures
    # workflows

    class Meta:
        app_label = "local_calculations"


class Individual(DatabaseTable):

    # Generation number
    # structure id
    # origin (source method)
    # fitness (field from output)
    # fingerprint (Q_entr, A_order, S_order)
    # Parent ID (optional)
    # Energy change (relative to parent)

    # instead of...
    #   structure
    #   structure_parent
    # maybe use...
    #   workflow
    #   workflow_parent
    #   fitness_field (property that points to workflow.final_structure.energy_per_atom)

    # timestamping for when this was added to the database
    created_at = table_column.DateTimeField(auto_now_add=True)

    # Algorithm used to create this structure
    source = table_column.ForeignKey(
        StructureSource,
        on_delete=table_column.CASCADE,
    )

    @classmethod
    def create_subclass_from_calculation(cls, name, calculation, **extra_columns):

        # There are the two columns we want to add to our table that both
        # link to some calculation table
        NewClass = cls.create_subclass(
            name,
            structure=table_column.OneToOneField(
                calculation,
                on_delete=table_column.CASCADE,
                primary_key=True,
            ),
            structure_parent=table_column.OneToOneField(
                calculation,
                on_delete=table_column.CASCADE,
                blank=True,
                null=True,
            ),
            **extra_columns,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewClass

    class Meta:
        abstract = True
        app_label = "local_calculations"


MITIndividuals = Individual.create_subclass_from_calculation(
    name="MITIndividuals",
    calculation=MITRelaxationStructure,
)


class StopCondition:
    pass  # TODO
