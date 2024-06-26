# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.data_explorer import views

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
        route="<provider_name>/about/",
        view=views.ProviderAPIViewSet.dynamic_about_view,
        name="provider-about",
    ),
    path(
        route="<provider_name>/<pk>/",
        view=views.ProviderAPIViewSet.dynamic_retrieve_view,
        name="entry-detail",
    ),
]
