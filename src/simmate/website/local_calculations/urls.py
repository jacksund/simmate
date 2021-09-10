# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.local_calculations import views

urlpatterns = [
    #
    # Lists off the different types of calculations
    path(
        route="",
        view=views.all_local_calculations,
        name="local_calculations",
    ),
    #
    # Lists off the different types of relaxations
    path(
        route="relaxations/",
        view=views.relaxations,
        name="relaxations",
    ),
    #
    # TODO: For now I list all calculation types here, but it will be useful
    # to have subapps that do this. I also want to incorporate dynamic loading
    # of the different options.
    path(
        route="relaxations/mit/",
        view=views.mit_about,
        name="mit_about",
    ),
    path(
        route="relaxations/mit/submit",
        view=views.mit_submit,
        name="mit_submit",
    ),
    path(
        route="relaxations/mit/results",
        view=views.mit_all,
        name="mit_all",
    ),
    path(
        route="relaxations/mit/results/<int:mitrelax_id>",
        view=views.mit_single,
        name="mit_single",
    ),
]
