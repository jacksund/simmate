# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path(
        route="",
        view=views.home,
        name="home",
    ),
]
