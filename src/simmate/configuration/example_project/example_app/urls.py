"""
Want to make a website interface for your app? Then you'll need to fill this file
out! If you ever venture to this level, we strongly recommend you go through the
django tutorials first: https://docs.djangoproject.com/en/3.2/

Note, we are working to have Simmate build this file for you automatically, but
that feature is still under early testing.
"""

from django.urls import path

from .views import example_view

urlpatterns = [
    path(
        route="",
        view=example_view,
        name="example_app",
    ),
]
