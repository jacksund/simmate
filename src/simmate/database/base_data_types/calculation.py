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
