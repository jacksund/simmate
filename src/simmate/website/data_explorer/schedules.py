from simmate.compute import schedule

from .models import TableCount
from .views import get_data_explorer_components


@schedule(interval="daily", at="02:00")
def run_update_table_counts():
    """
    Nightly task to update the table counts cache.

    Iterates through all datasets configured for the Data Explorer and
    caches their row counts in the TableCount model to prevent slow queries
    on the website's homepage.
    """
    for components in get_data_explorer_components().values():
        for component in components:
            table = component.table
            count = table.objects.count()
            TableCount.objects.update_or_create(
                table_name=table.table_name,  # so it's not the full path
                defaults={"row_count": count},
            )
