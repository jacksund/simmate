# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path(
        route="",
        view=views.home,
        name="home",
    ),
    path(
        route="<table_name>/",
        view=views.DynamicDatabaseTableView.as_view(),
        name="database_table",
    ),
    path(
        route="<provider_name>/about/",
        # view=views.ProviderAPIViewSet.dynamic_about_view,
        view=views.DynamicDatabaseTableView.as_view(),
        name="database_table-about",
    ),
    path(
        route="<provider_name>/<pk>/",
        # view=views.ProviderAPIViewSet.dynamic_retrieve_view,
        view=views.DynamicDatabaseTableView.as_view(),
        name="entry-detail",
    ),
]
