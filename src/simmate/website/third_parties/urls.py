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
        view=views.ProviderAPIViewSet.dynamic_list_view,
        name="provider",
    ),
    path(
        route="<provider_name>/<pk>/",
        view=views.ProviderAPIViewSet.dynamic_retrieve_view,
        name="entry-detail",
    ),
]
