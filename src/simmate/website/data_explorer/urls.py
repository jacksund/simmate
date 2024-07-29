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
        route="<provider_name>/about/",
        view=views.DataExplorerView.about_view,
        name="table-about",
    ),
    path(
        route="<provider_name>/<pk>/",  # BUG: if pk == "about"
        view=views.DataExplorerView.entry_view,
        name="table-entry",
    ),
]
