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
        view=views.DataExplorerView.list_view,
        name="table",
    ),
    path(
        route="<table_name>/about/",
        view=views.DataExplorerView.about_view,
        name="table-about",
    ),
    path(
        route="<table_name>/new/",
        view=views.DataExplorerView.entry_new_view,
        name="table-entry-new",
    ),
    path(
        route="<table_name>/search/",
        view=views.DataExplorerView.search_view,
        name="table-search",
    ),
    path(
        # BUG: if table_entry_id in ["about", "new", "search"]
        route="<table_name>/<table_entry_id>/",
        view=views.DataExplorerView.entry_view,
        name="table-entry",
    ),
    path(
        route="<table_name>/<table_entry_id>/update/",
        view=views.DataExplorerView.entry_update_view,
        name="table-entry-update",
    ),
]
