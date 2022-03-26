# -*- coding: utf-8 -*-

from django.urls import path
from simmate.website.third_parties import views


urlpatterns = [
    path(
        route="",
        view=views.providers_all,
        name="home",
    ),
    path(
        route="<provider_name>/",
        view=views.provider,
        name="provider",
    ),
    path(
        route="<provider_name>/<entry_id>/",
        view=views.entry_detail,
        name="entry-detail",
    ),
]
