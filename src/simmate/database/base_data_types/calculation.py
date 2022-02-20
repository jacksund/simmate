# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class Calculation(DatabaseTable):
    """
    A calculation is synonmyous with a Prefect "Flow-Run". This entire table together
    can be viewed as the "Flow" which may have extra metadata. This could
    include values such as...
        - workflow_name
        - simmate_version
        - [[thirdparty]]_version (i.e. vasp_version="5.4.4")
    """

    class Meta:
        abstract = True
        app_label = "local_calculations"

    base_info = [
        "directory",
        "prefect_flow_run_id",
        "created_at",
        "updated_at",
        "corrections",
    ]

    directory = table_column.CharField(
        max_length=250,
        blank=True,
        null=True,
    )
    """
    This is the folder that the workflow was ran in. It will be something
    like... "/path/to/simmate-task-abc123"
    """
    # TODO: maybe add host computer name too? (via platform.node())

    prefect_flow_run_id = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )
    """
    If this was submitted through Prefect, there is a lot more metadata available
    for this calculation. Simmate does not store this data directly, but instead
    we store the flow-run-id so that the user may look this up in the Prefect
    database if they wish.
    An example id is... d8a785e1-e344-463a-bede-0e7b3da7bab6
    """

    created_at = table_column.DateTimeField(auto_now_add=True)
    """
    timestamping for when this was added to the database
    """

    updated_at = table_column.DateTimeField(auto_now=True)
    """
    timestamping for when this was last updated
    """

    corrections = table_column.JSONField(blank=True, null=True)
    """
    Simmate workflows often have ErrorHandlers that fix any issues while the
    calaculation ran. This often involves changing settings, so we store
    any of those changes here.
    """

    # EXPERIMENTAL
    # Where this calculation plays a role within a "nested" workflow calculation.
    # Becuase this structure can be reused by multiple workflows, we make this
    # a list of source-like objects. For example, a relaxation could be part of
    # a series of relaxations (like in StagedRelaxation) or it can be an initial
    # step of a BandStructure calculation.
    # parent_nested_calculations = table_column.JSONField(blank=True, null=True)

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
    def prefect_cloud_link(self) -> str:
        """
        URL to this calculation (flow-run) in the Prefect Cloud webstite.
        """
        return f"https://cloud.prefect.io/simmate/flow-run/{self.prefect_flow_run_id}"

    """ Model Methods """

    @classmethod
    def from_prefect_id(cls, id: str, **kwargs):
        """
        Given a prefect id, this method will do one of the following...

        1. if it exists, load the database object with matching prefect_id
        2. if it doesn't exist, create a new database object using this ID and extra kwargs

        """

        # Depending on how a workflow was submitted, there may be a calculation
        # extry existing already -- which we need to grab and then update. If it's
        # not there, we create a new one!

        # check if the calculation already exists in our database, and if so,
        # grab it and return it.
        if cls.objects.filter(prefect_flow_run_id=id).exists():
            return cls.objects.get(prefect_flow_run_id=id)
        # Otherwise we need to create a new one and return that.

        # To handle the initialization of other Simmate mix-ins, we pass all
        # information to the from_toolkit method rather than directly to cls.
        calculation = cls.from_toolkit(prefect_flow_run_id=id, **kwargs)
        calculation.save()

        return calculation
