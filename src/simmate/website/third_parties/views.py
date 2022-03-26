# -*- coding: utf-8 -*-

from django.shortcuts import render

from simmate.database import third_parties
from simmate.website.core_components.utilities import render_from_table


def providers_all(request):

    # TODO: auto determine this list and descriptions
    workflows_metadata = {
        # "AflowStructure": (
        #     "These workflows calculate the energy for a structure. In many cases, "
        #     "this also involves calculating the lattice strain and forces for each site."
        # ),
        "CodStructure": "...",
        "JarvisStructure": "...",
        "MatProjStructure": "...",
        "OqmdStructure": "...",
    }

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "third_parties",
        "workflows_metadata": workflows_metadata,
    }
    template = "third_parties/providers_all.html"
    return render(request, template, context)


def provider(request, provider_name: str):

    # using the provider name (which is really just the table name), load
    # the corresponding database table
    provider_table = getattr(third_parties, provider_name)

    return render_from_table(
        request=request,
        template="third_parties/provider.html",
        context={"active_tab_id": "third_parties", "provider": provider_table},
        table=provider_table,
        view_type="list",
    )


def entry_detail(
    request,
    provider_name: str,
    entry_id: int,
):

    # using the provider name (which is really just the table name), load
    # the corresponding database table
    provider_table = getattr(third_parties, provider_name)

    return render_from_table(
        request=request,
        request_kwargs={
            "provider_name": provider_name,
            "entry_id": entry_id,
        },
        template="third_parties/entry_detail.html",
        context={"active_tab_id": "extras"},
        table=provider_table,
        view_type="retrieve",
        primary_key_url="entry_id",
    )
