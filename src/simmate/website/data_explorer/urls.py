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
        view=views.table_entries,
        name="table",
    ),
    path(
        route="<table_name>/about/",
        view=views.table_about,
        name="table-about",
    ),
    path(
        route="<table_name>/new/",
        view=views.table_entry_new,
        name="table-entry-new",
    ),
    path(
        route="<table_name>/new-many/",
        view=views.table_entry_new_many,
        name="table-entry-new-many",
    ),
    # Note: an `update-many` view does not exists bc it doesn't make sense to
    # have it as a standalone page outside of the `table` view
    path(
        route="<table_name>/search/",
        view=views.table_search,
        name="table-search",
    ),
    path(
        # BUG: if table_entry_id in ["about", "new", "search"]
        route="<table_name>/<table_entry_id>/",
        view=views.table_entry,
        name="table-entry",
    ),
    path(
        route="<table_name>/<table_entry_id>/update/",
        view=views.table_entry_update,
        name="table-entry-update",
    ),
]
