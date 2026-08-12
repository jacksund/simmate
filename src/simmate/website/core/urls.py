# -*- coding: utf-8 -*-

from django.urls import path

from simmate.compute.api import views as compute_api_views

urlpatterns = [
    path(
        route="compute/work_items/next/",
        view=compute_api_views.get_next_work_item,
        name="api_get_next_work_item",
    ),
    path(
        route="compute/work_items/<uuid:work_item_id>/update/",
        view=compute_api_views.update_work_item,
        name="api_update_work_item",
    ),
]
