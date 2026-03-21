# -*- coding: utf-8 -*-

from schedule import every, repeat

from simmate.config import settings
from simmate.database.utilities import get_table

from .models import TableCount


@repeat(every().day.at("02:00"))
def run_update_table_counts():
    """
    Nightly task to update the table counts cache.

    Iterates through all datasets configured for the Data Explorer and
    caches their row counts in the TableCount model to prevent slow queries
    on the website's homepage.
    """
    for section_name, table_list in settings.website.data.items():
        for table_name in table_list:
            table = get_table(table_name)
            count = table.objects.count()
            TableCount.objects.update_or_create(
                table_name=table.table_name,  # so it's not the full path
                defaults={"row_count": count},
            )
