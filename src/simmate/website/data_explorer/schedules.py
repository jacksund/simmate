# -*- coding: utf-8 -*-

from schedule import every, repeat

from simmate.config import settings

from .models import TableCount


@repeat(every().day.at("02:00"))
def run_update_table_counts():
    """
    Nightly task to update the table counts cache.

    Iterates through all datasets configured for the Data Explorer and
    caches their row counts in the TableCount model to prevent slow queries
    on the website's homepage.
    """
    from .views import get_data_explorer_components

    for section_name, components in get_data_explorer_components().items():
        for component in components:
            table = component.table
            count = table.objects.count()
            TableCount.objects.update_or_create(
                table_name=table.table_name,  # so it's not the full path
                defaults={"row_count": count},
            )
