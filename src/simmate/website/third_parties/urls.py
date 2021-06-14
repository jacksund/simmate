# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.third_parties import views

app_name = "third_parties"
urlpatterns = [
    # This is the main page for this app.
    path(
        route="",
        view=views.home,
        name="third_parties_home",
    ),
]
