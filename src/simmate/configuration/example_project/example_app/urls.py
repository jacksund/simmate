"""
This file takes the functions in `views.py` and maps them to an actual website URL.
So... if you delete/update `views.py`, then this file should be updated accordingly.

If you ever venture to this level, we STRONGLY recommend you go through the
django tutorials first: https://docs.djangoproject.com/en/3.2/
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

# NOTE: You can delete this file if you decide not to use it.
