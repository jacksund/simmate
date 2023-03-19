# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.database.base_data_types import DatabaseTable
from simmate.website.core_components.base_api_view import SimmateAPIViewSet
from simmate.configuration.django.settings import SIMMATE_DATA


ALL_PROVIDERS = {
    DatabaseTable.get_table(table_name).table_name: DatabaseTable.get_table(table_name) 
    for table_name in SIMMATE_DATA
}


def providers_all(request):
    context = {"all_providers": ALL_PROVIDERS.values()}
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
        return {"provider": provider_table}

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
