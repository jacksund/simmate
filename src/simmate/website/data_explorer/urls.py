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
        route="<table_name>/<table_entry_id>/",  # BUG: if pk == "about"
        view=views.DataExplorerView.entry_view,
        name="table-entry",
    ),
]
