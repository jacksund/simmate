from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import F

from simmate.database.core import DatabaseTable, table_column

from .batch import Batch
from .container import Container


class UsageLog(DatabaseTable):
    """
    A record of material being removed from a container, such as a user
    taking some material for an experiment or synthesis.
    """

    class Meta:
        db_table = "inventory_management__usage_logs"

    # -------------------------------------------------------------------------

    source_container = table_column.ForeignKey(
        Container,
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="usage_logs",
    )
    """
    The container that the material was removed from.
    """

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        null=True,
        blank=True,
        related_name="usage_logs",
    )
    """
    The user that removed the material.
    """

    amount_removed = table_column.DecimalField(
        max_digits=16,
        decimal_places=3,
    )
    """
    The amount of material removed, in the `amount_units` of the
    `source_container`.
    """

    comments = table_column.TextField(
        blank=True,
        null=True,
    )
    """
    Any extra notes about this usage (e.g. what the material was used for).
    """

    # -------------------------------------------------------------------------

    destination_batch = table_column.ForeignKey(
        Batch,
        on_delete=table_column.SET_NULL,
        null=True,
        blank=True,
        related_name="source_usage_logs",
    )
    """
    The batch this material was used to make, if any (e.g. the product of a
    synthesis that consumed this material)
    """

    # -------------------------------------------------------------------------

    def deduct_from_container(self, mark_depleted: bool = False):
        """
        Removes `amount_removed` from the source container's `current_amount`
        and then updates the cached columns of that container's batch. Call
        this once, right after a new usage log is saved.

        Args:
            mark_depleted: Whether to also mark the source container as
                depleted (e.g. when it is now empty).
        """
        # form inputs can give a float, which can't be combined with a decimal
        amount = Decimal(str(self.amount_removed))
        containers = Container.objects.filter(id=self.source_container_id)
        updates = dict(current_amount=F("current_amount") - amount)
        if mark_depleted:
            updates["is_depleted"] = True
        containers.update(**updates)

        Batch.update_cached_columns(containers.values_list("batch_id", flat=True))

    # -------------------------------------------------------------------------
