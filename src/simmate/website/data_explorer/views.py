# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, Structure
from simmate.website.core_components.base_api_view_dev import DatabaseTableView

# closed-source data types. We can skip these if they aren't present
try:
    from simmate_corteva.rdkit.models import Molecule
except ModuleNotFoundError:
    Molecule = None  # dummy class just for comparison below


# BUG: fails if tables from different apps have the same name
EXPLORABLE_TABLES = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for table_name in settings.website.data
}


def home(request):
    crystal_dbs = []
    molecular_dbs = []
    other_dbs = []
    for table in EXPLORABLE_TABLES.values():
        if issubclass(table, Structure):
            crystal_dbs.append(table)
        elif Molecule and issubclass(table, Molecule):
            molecular_dbs.append(table)
        else:
            other_dbs.append(table)

    context = {
        "all_datasets": {
            "Molecular": molecular_dbs,
            "Crystalline": crystal_dbs,
            "Other": other_dbs,
        },
        "breadcrumb_active": "Data",
    }
    template = "data_explorer/home.html"
    return render(request, template, context)


class DynamicDatabaseTableView(DatabaseTableView):

    # TODO: these are not used. will move to base databasetable class
    # template_about = "data_explorer/about.html"
    # template_list = "data_explorer/provider.html"
    # template_retrieve = "data_explorer/entry_detail.html"

    @classmethod
    def get_table(cls, request, table_name: str) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        provider_table = EXPLORABLE_TABLES[table_name]
        return provider_table


# entry_id: int | str = None,  # type depends on table's primary key column
