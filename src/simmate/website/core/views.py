# -*- coding: utf-8 -*-

import importlib

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.shortcuts import render

from simmate.configuration import settings
from simmate.database.third_parties import (
    AflowStructure,
    CodStructure,
    JarvisStructure,
    MatprojStructure,
    OqmdStructure,
)
from simmate.utilities import get_app_submodule, get_class
from simmate.website.data_explorer.forms import ChemicalSystemForm

# -----------------------------------------------------------------------------

# this section is wacky because we want to dynamically set the home and profile
# fxn/views using either a default or some env variable (which allows people
# to override it)


@login_required
def profile_default_view(request):
    # !!! For future reference, you can grab user-associated data via...
    # data = request.user.relateddata.all()

    context = {}
    template = "account/profile.html"
    return render(request, template, context)


@login_required
def profile(request):
    if not settings.website.profile_view:
        return profile_default_view(request)  # This is the function above
    else:
        # we assume the view is named "profile" inside this module
        profile_module = importlib.import_module(settings.website.profile_view)
        profile_view = getattr(profile_module, "profile")
        return profile_view(request)


def home_default_view(request):
    # The default homepage is a bulk query for crystal structures. For internal
    # websites, a different homepage (e.g. a chatbot) is used instead.

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
            cleaned_data = form.cleaned_data

            # check which databases the user wants to search and collect the
            # proper models into a list that we query with below
            databases_to_search = []
            for database, database_model in (
                ("aflow", AflowStructure),
                ("cod", CodStructure),
                ("jarvis", JarvisStructure),
                ("materials_project", MatprojStructure),
                ("oqmd", OqmdStructure),
            ):
                # if the user requested this database, the value will be true
                if cleaned_data[database]:
                    databases_to_search.append(database_model)

            # Note, this value is converted to a list of systems once cleaned.
            chemical_systems = cleaned_data["chemical_system"]

            # now go through each database, search for the requested system
            # and then pool them all together. We limit each database to 50
            # results. Note the += below means we compile into a single list
            structures = []
            nstructures_possible = 0
            for database_model in databases_to_search:
                # Now we can make the query! We also dont want to load the
                # structure json -- so that everything runs faster.
                search_results = database_model.objects.filter(
                    chemical_system__in=chemical_systems
                ).defer("structure")

                # if the database provides the hull energy, we want to sort
                # the structures by that (putting highest priority on stable ones)
                if hasattr(database_model, "energy_above_hull"):
                    # if there isn't a hull energy value, place these last
                    search_results = search_results.order_by(
                        F("energy_above_hull").asc(nulls_last=True)
                    )

                # now add the search results to the output
                # for performance, we limit each database to 50 structures
                structures += search_results.all()[:50]

                # We also tell the user how many results are possible if there
                # wasn't any limit on the structures returned
                nstructures_possible += database_model.objects.filter(
                    chemical_system__in=chemical_systems,
                ).count()

    # if the page is grabbed via a 'GET' method, send an empty form
    else:
        # otherwise we are giving an empty form and no result structures
        form = ChemicalSystemForm()
        structures = None
        nstructures_possible = None

    # now let's put the data and template together to send the user
    context = {
        "chemical_system_form": form,
        "structures": structures,
        "nstructures_possible": nstructures_possible,
    }
    template = "home/home.html"
    return render(request, template, context)


def home(request):
    if not settings.website.home_view:
        return home_default_view(request)  # This is the function above
    else:
        # we assume the view is named "home" inside this module
        home_module = importlib.import_module(settings.website.home_view)
        home_view = getattr(home_module, "home")
        return home_view(request)


# -----------------------------------------------------------------------------


def loginstatus(request):
    context = {}
    template = "account/loginstatus.html"
    return render(request, template, context)


def permission_denied(request):
    raise PermissionDenied


def apps(request):
    extra_apps = []
    for app_name in settings.apps:
        urls_path = get_app_submodule(app_name, "urls")
        if urls_path:
            app_config = get_class(app_name)
            extra_apps.append(
                {
                    "verbose_name": app_config.verbose_name,
                    "short_name": app_config.name.split(".")[-1],
                    "description_short": app_config.description_short,
                }
            )
    context = {"extra_apps": extra_apps}
    template = "core_components/apps.html"
    return render(request, template, context)


def extras(request):
    context = {}
    template = "core_components/extras.html"
    return render(request, template, context)


def contact(request):
    context = {}
    template = "core_components/contact.html"
    return render(request, template, context)


def about(request):
    context = {}
    template = "core_components/about.html"
    return render(request, template, context)
