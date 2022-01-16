# -*- coding: utf-8 -*-

from django.urls import include, path

from rest_framework import routers

from simmate.website.rest_api.views import (
    SpacegroupViewSet,
    MatProjViewSet,
    JarvisViewSet,
    AflowViewSet,
    OqmdViewSet,
    CodViewSet,
)


router = routers.DefaultRouter()
router.register("space-groups", SpacegroupViewSet)
router.register("materials-project", MatProjViewSet)
router.register("jarvis", JarvisViewSet)
router.register("aflow", AflowViewSet)
router.register("oqmd", OqmdViewSet)
router.register("cod", CodViewSet)

urlpatterns = [
    # Our router automatically handle each possible endpoint for us! We stick
    # with the default REST templates and views too.
    path(
        route="",
        view=include(router.urls),
        # name="api-root", # This is set by default
        # To view all other urls that this maps, you can use django_extensions
        # to list all of them. The command is... python manage.py show_urls
    ),
    #
    # Additionally, we include login URLs. This doesn't do anything other than
    # let the user login on the default REST interface.
    path(
        route="accounts/",
        view=include("rest_framework.urls"),
        name="rest_login",
    ),
]
