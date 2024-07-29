# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.data_explorer import views

from simmate.website.core_components.base_api_view_dev import DatabaseTableView

urlpatterns = [
    path(
        route="",
        view=views.providers_all,
        name="home",
    ),
    path(
        route="provider-dev/",
        view=DatabaseTableView.as_view(),
        name="provider-dev",
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
