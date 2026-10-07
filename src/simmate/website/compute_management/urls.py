# -*- coding: utf-8 -*-

from django.urls import path

from simmate.compute.api import views as api_views

from . import views

urlpatterns = [
    path(route="", view=views.home, name="home"),
    # REST endpoints used by remote `ApiWorker`s
    path(
        route="workers/check/",
        view=api_views.check_worker_access,
        name="api_check_worker_access",
    ),
    path(
        route="work_items/next/",
        view=api_views.get_next_work_item,
        name="api_get_next_work_item",
    ),
    path(
        route="work_items/<uuid:work_item_id>/update/",
        view=api_views.update_work_item,
        name="api_update_work_item",
    ),
]
