# -*- coding: utf-8 -*-

from django.urls import include, path

from rest_framework import routers

from simmate.website.rest_api.views import (
    MaterialsProjectViewSet,
    JarvisViewSet,
    AflowViewSet,
    OqmdViewSet,
    CodViewSet,
)


router = routers.DefaultRouter()
router.register("materials-project", MaterialsProjectViewSet)
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
        name="rest_endpoints",
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
