# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class Calculation(DatabaseTable):

    # A calculation is synonmyous with a "Flow-Run". This entire table together
    # can be viewed as the "Flow" which may have extra metadata. This could
    # include values such as...
    #   workflow_name
    #   simmate_version
    #   [[thirdparty]]_version (i.e. vasp_version="5.4.4")

    """Base info"""

    # This is the folder that the workflow was ran in. It will be something
    # like... "/path/to/simmate-task-abc123"
    directory = table_column.CharField(
        max_length=250,
        blank=True,
        null=True,
    )
    # TODO: maybe add host computer name too? (via platform.node())

    # If this was submitted through Prefect, there is a lot more metadata available
    # for this calculation. Simmate does not store this data directly, but instead
    # we store the flow-run-id so that the user may look this up in the Prefect
    # database if they wish.
    # An example id is... d8a785e1-e344-463a-bede-0e7b3da7bab6
    prefect_flow_run_id = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )

    # timestamping for when this was added to the database
    created_at = table_column.DateTimeField(auto_now_add=True)
    updated_at = table_column.DateTimeField(auto_now=True)

    # Simmate workflows often have ErrorHandlers that fix any issues while the
    # calaculation ran. This often involves changing settings, so we store
    # any of those changes here.
    corrections = table_column.JSONField(blank=True, null=True)

    """Archived Data"""
    # I may want to add these fields because Prefect doesn't store run stats
    # indefinitely AND it doesn't give detail memory use, number of cores, etc.
    # If all of these are too much, I could do a json field of "run_stats" instead

    # average_memory (The average memory used in kb)
    # max_memory (The maximum memory used in kb)
    # elapsed_time (The real time elapsed in seconds)
    # system_time(The system CPU time in seconds)
    # user_time(The user CPU time spent by VASP in seconds)
    # total_time (The total CPU time for this calculation)
    # cores (The number of cores used by VASP (some clusters print `mpi-ranks` here))

    # Here are some other Prefect fields too.
    # agent_id
    # auto_scheduled
    # context
    # created_by_user_id
    # end_time
    # flow_id
    # labels
    # name
    # parameters
    # scheduled_start_time
    # start_time
    # state
    # tenant_id
    # times_resurrected
    # version

    """ Relationships """
    # While there are no base relations for this abstract class, the majority of
    # calculations will link to a structure or alternatively a diffusion pathway
    # or crystal surface. In such cases, you'll add a relationship like this:
    #
    #   structure = table_column.ForeignKey(
    #       ExampleStructureModel,
    #       on_delete=table_column.CASCADE,
    #   )
    #
    # Note that this is a ForeignKey because we want to allow the user to attempt
    # the same calculation multiple times. Otherwise it would be a OneToOneField.

    """ Properties """

    @property
    def prefect_cloud_link(self):
        return f"https://cloud.prefect.io/simmate/flow-run/{self.prefect_flow_run_id}"

    """ Model Methods """

    @classmethod
    def from_prefect_id(cls, id, **kwargs):
        # Depending on how a workflow was submitted, there may be a calculation
        # extry existing already -- which we need to grab and then update. If it's
        # not there, we create a new one!

        # check if the calculation already exists in our database, and if so,
        # grab it and return it.
        if cls.objects.filter(prefect_flow_run_id=id).exists():
            return cls.objects.get(prefect_flow_run_id=id)
        # Otherwise we need to create a new one and return that.

        # See if the calculation table has a from_pymatgen method (most simmate calcs do)
        # and if so, we should call that instead and pass all of our kwargs to it.
        if hasattr(cls, "from_pymatgen"):

            calculation = cls.from_pymatgen(prefect_flow_run_id=id, **kwargs)
        else:
            calculation = cls(prefect_flow_run_id=id, **kwargs)
        calculation.save()

        return calculation

    """ Restrictions """
    # none

    """ For website compatibility """
    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need its own
    # table. Therefore, I set this as an abstract model. Should that change in the
    # future, look here:
    # https://docs.djangoproject.com/en/3.1/topics/db/models/#model-inheritance
    class Meta:
        abstract = True
        app_label = "local_calculations"


# EXPERIMENTAL
class NestedCalculation(Calculation):
    """
    A nested calculation is a calculation made up of other calculations. For example,
    we may want to run a workflow that runs a series of relaxations. Or maybe
    a relaxation, then energy, then bandstrucuture calculation. This table
    is for keeping track of workflows ran in series like this.
    """

    class Meta:
        abstract = True
        app_label = "local_calculations"

    # @abstractproperty
    # child_calculation_tables = [...]

    # TODO:
    # corrections
    # should this be a list of all modifications? It could maybe be used to
    # carry fixes (such as smearing) accross different calcs.
    # Or maybe a method that just lists the corrections of each subcalc?
    # For now I don't use this though. This line removes the field.
    corrections = None

    @classmethod
    def create_subclass_from_calcs(
        cls, name, child_calculation_tables, module, **extra_columns
    ):

        # BUG: I assume a workflow won't point to the save calculation table
        # more than once... What's a scenario where this isn't true?
        # I can only think of mult-structure workflows (like EvolutionarySearch)
        # which I don't give their own table for now.
        new_columns = {}
        for child_calc in child_calculation_tables:
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
            child_calculation_tables=child_calculation_tables,
            module=module,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewClass

    def update_calculation(self):
        
        raise Exception(
            "NestedCalculation datatable is experimental so this method doesn't "
            "work yet."
        )
        
        # BUG: This assumes we ran all calculations within the same directory,
        # which isn't true in all cases.
        for child_calc_table in self.child_calculation_tables:
            if child_calc_table.objects.filter(directory=self.directory).exists():
                child_calc = child_calc_table.objects.get(directory=self.directory)
                setattr(self, child_calc._meta.model_name, child_calc)
        self.save()
