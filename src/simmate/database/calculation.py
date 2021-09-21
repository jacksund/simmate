# -*- coding: utf-8 -*-

from simmate.database.base import DatabaseTable, table_column


class Calculation(DatabaseTable):

    # A calculation is synonmyous with a "Flow-Run". This entire table together
    # can be viewed as the "Flow" which may have extra metadata. This could
    # include values such as...
    #   workflow_name
    #   simmate_version
    #   [[thirdparty]]_version (i.e. vasp_version="5.4.4")

    """Base info"""

    # If this was submitted through Prefect, there is a lot more metadata available
    # for this calculation. Simmate does not store this data directly, but instead
    # we store the flow-run-id so that the user may look this up in the Prefect
    # database if they wish.
    # I store the name because it's shorter and user friendly. For example,
    #   name = jolly-hornet
    #   id = d8a785e1-e344-463a-bede-0e7b3da7bab6
    # The id is still needed because it let's me make the link to the cloud page
    prefect_flow_run_name = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    prefect_flow_run_id = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    prefect_flow_run_version = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    # Indicate what state the calculation is in. This exists to ensure we don't
    # submit multiple to Prefect and also let's us check how many currently exist in
    # the queue.
    # !!! If you choose to change these, consider Prefect's different state labels:
    #       https://docs.prefect.io/api/latest/engine/state.html
    # class StatusTypeOptions(table_column.TextChoices):
    #     SCHEDULED = "S"
    #     COMPLETED = "C"
    #     FAILED = "F"

    # status = table_column.CharField(
    #     max_length=1,
    #     choices=StatusTypeOptions.choices,
    #     default=StatusTypeOptions.SCHEDULED,
    # )

    # timestamping for when this was added to the database
    created_at = table_column.DateTimeField(auto_now_add=True)
    updated_at = table_column.DateTimeField(auto_now=True)

    # Simmate workflows often have ErrorHandlers that fix any issues while the
    # calaculation ran. This often involves changing settings, so we store
    # any of those changes here.
    corrections = table_column.JSONField(blank=True, null=True)

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
    # Note that this is a ForeignKey because we want to all the user to attempt
    # the same calculation multiple times. Otherwise it would be a OneToOneField.

    """ Properties """

    @property
    def prefect_cloud_link(self):
        return f"https://cloud.prefect.io/simmate/flow-run/{self.prefect_flow_run_id}"

    """ Model Methods """

    @classmethod
    def from_prefect_context(cls, prefect_context, **kwargs):
        # Given a Prefect context, this will return a database calculation
        # object, but will NOT save it to the database yet. The kwargs input
        # is only if you inherit from this class and add extra fields.
        calculation = cls(
            prefect_flow_run_name=prefect_context.flow_run_name,
            prefect_flow_run_id=prefect_context.flow_run_id,
            prefect_flow_run_version=prefect_context.get("flow_run_version"),
            **kwargs,
        )
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
