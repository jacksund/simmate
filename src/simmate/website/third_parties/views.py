# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.database import third_parties
from simmate.database.base_data_types import DatabaseTable
from simmate.website.core_components.base_api_view import SimmateAPIViewSet


def providers_all(request):

    # TODO: auto determine this list and descriptions
    workflows_metadata = {
        # "AflowStructure": "...",  # not allowed to redistribute
        "AflowPrototype": "...",
        "CodStructure": "...",
        "JarvisStructure": "...",
        "MatprojStructure": "...",
        "OqmdStructure": "...",
    }

    # now let's put the data and template together to send the user
    context = {"workflows_metadata": workflows_metadata}
    template = "third_parties/providers_all.html"
    return render(request, template, context)


class ProviderAPIViewSet(SimmateAPIViewSet):

    template_list = "third_parties/provider.html"
    template_retrieve = "third_parties/entry_detail.html"

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
        provider_table = getattr(third_parties, provider_name)
        return provider_table

    def get_list_context(
        self,
        request,
        provider_name,
    ) -> dict:

        provider_table = getattr(third_parties, provider_name)
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
