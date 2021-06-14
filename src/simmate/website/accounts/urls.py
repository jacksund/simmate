# -*- coding: utf-8 -*-

# django has builtin views for login/logout/etc
# import if you want to setup login/logout views with more control
# from django.contrib.auth import views as auth_views

from django.urls import include, path

from simmate.website.accounts import views

urlpatterns = [
    # This points to a built-in app for django that has the some login/password options
    # https://docs.djangoproject.com/en/3.0/topics/auth/default/#module-django.contrib.auth.views
    path(route="", view=include("django.contrib.auth.urls")),
    # the include() here maps the following:
    #   accounts/login/ [name='login']
    #   accounts/logout/ [name='logout']
    #   accounts/password_change/ [name='password_change']
    #   accounts/password_change/done/ [name='password_change_done']
    #   accounts/password_reset/ [name='password_reset']
    #   accounts/password_reset/done/ [name='password_reset_done']
    #   accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
    #   accounts/reset/done/ [name='password_reset_complete']
    # The built-in app doesn't provide a way to create new users though
    path(
        route="register/",
        view=views.register,
        name="register",
    ),
    # On login success, you will be pointed to /accounts/profile by default,
    # but this isn't mapped. If you want to change this defualt, then
    # set LOGIN_REDIRECT_URL in the settings.py file
    path(
        route="profile/",
        view=views.profile,
        name="profile",
    ),
    # When you point to the url 'logout', it signs you out and then sends you
    # to LOGOUT_REDIRECT_URL (set in settings.py)
    path(
        route="loginstatus/",
        view=views.loginstatus,
        name="loginstatus",
    ),
]
