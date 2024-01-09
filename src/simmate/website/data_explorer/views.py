# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable, Structure
from simmate.website.core_components.base_api_view import SimmateAPIViewSet

# closed-source data types. We can skip these if they aren't present
try:
    from simmate_corteva.rdkit.models import Molecule
except ModuleNotFoundError:
    Molecule = None  # dummy class just for comparison below


ALL_PROVIDERS = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name)
    for table_name in settings.website.data
}


def providers_all(request):
    crystal_dbs = []
    molecular_dbs = []
    other_dbs = []
    for table in ALL_PROVIDERS.values():
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
        }
    }
    template = "data_explorer/providers_all.html"
    return render(request, template, context)


class ProviderAPIViewSet(SimmateAPIViewSet):
    template_list = "data_explorer/provider.html"
    template_retrieve = "data_explorer/entry_detail.html"

    @classmethod
    def get_table(
        cls,
        request,
        provider_name,
        pk=None,
    ) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        # using the provider name (which is really just the table name), load
        # the corresponding database table
        #   provider_table = DatabaseTable.get_table(provider_name)
        provider_table = ALL_PROVIDERS[provider_name]
        return provider_table

    def get_list_context(
        self,
        request,
        provider_name,
    ) -> dict:
        provider_table = ALL_PROVIDERS[provider_name]
        return {
            "provider": provider_table,
            **provider_table.extra_html_context,
        }

    def get_retrieve_context(
        self,
        request,
        provider_name,
        pk,
    ) -> dict:
        return {
            "provider_name": provider_name,
            "entry_id": pk,
        }
