# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable
from simmate.website.core_components.base_api_view_dev import DynamicApiView


# BUG: fails if tables from different apps have the same name
EXPLORABLE_TABLES = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for section_name, table_names in settings.website.data.items()
    for table_name in table_names
}


def get_data_config():
    # keeps dict organizization, but replaces strings with the actual db table
    data_config = {}
    for section_name, table_list in settings.website.data.items():
        data_config[section_name] = [
            DatabaseTable.get_table(table_name) for table_name in table_list
        ]
    return data_config


DATA_CONFIG = get_data_config()


def home(request):
    context = {
        "data_config": DATA_CONFIG,
        "breadcrumb_active": "Data",
    }
    template = "data_explorer/home.html"
    return render(request, template, context)


class DataExplorerView(DynamicApiView):

    @classmethod
    def get_table(
        cls,
        request,
        table_name: str,
        table_entry_id: int | str = None,  # type depends on table's primary key column
    ) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        provider_table = EXPLORABLE_TABLES[table_name]
        return provider_table
