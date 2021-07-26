# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect

from simmate.website.third_parties.forms import ChemicalSystemForm

from simmate.database.third_parties.all import (
    MaterialsProjectStructure,
    JarvisStructure,
    AflowStructure,
    OqmdStructure,
    CodStructure,
)


def home(request):

    # The home page is also an html "form" because users submit queries from
    # here. So we need to handle form submissions properly.

    # first check if the webpage is accessed via a POST method
    if request.method == "POST":
        # if it is, that means a user is trying to submit a query
        # let's grab the data and validate it before running the query
        form = ChemicalSystemForm(request.POST)
        # see if all of the data is valid
        if form.is_valid():
            # grab the cleaned data from the form
            # Note, this value is converted to a list of systems once cleaned.
            chemical_systems = form.cleaned_data["chemical_system"]
            print(chemical_systems)
            # Now we can make the query! We limit the results to only 200 structures
            # to make things easier on our server.
            # TODO: Should I sort by stability or something else?
            # TODO: This is only the materials project for now.
            structures = MaterialsProjectStructure.objects.filter(
                chemical_system__in=chemical_systems,
            ).all()[:200]
    
    # if the page is grabbed via a 'GET' method, send an empty form
    else:
        # otherwise we are giving an empty form and no result structures
        form = ChemicalSystemForm()
        structures = None

    # now let's put the data and template together to send the user
    context = {
        "active_tab_id": "home",
        "chemical_system_form": form,
        "structures": structures,
    }
    template = "core/home.html"
    return render(request, template, context)
