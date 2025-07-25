"""
Defines all Django settings for Simmate.

Note, some settings are dynamically determined, such as the installed apps and
database backend being used.
"""

import os

from simmate.configuration import settings
from simmate.utilities import get_directory

# --------------------------------------------------------------------------------------

DEBUG = settings.website.debug

ALLOWED_HOSTS = settings.website.allowed_hosts

CSRF_TRUSTED_ORIGINS = settings.website.csrf_trusted_origins

SECRET_KEY = settings.website.secret_key

# --------------------------------------------------------------------------------------

# DATABASE CONNECTION
_default_database = {k.upper(): v for k, v in settings.database.items()}
DATABASES = {"default": _default_database}

# List all applications that Django will initialize with. Write the full python
# path to the app or it's config file. Note that relative python paths work too
# if you are developing a new app.
INSTALLED_APPS = [
    #
    # These are built-in django apps that we use for extra features
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    # Other apps installed with Django to consider
    #   "django.contrib.postgres",
    #   "django.contrib.redirects",
    #   "django.contrib.sitemaps",
    #
    # Apps for django-allauth that allow sign-on using external accounts
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # note: there are extra apps installed based on configuration. See the
    # allauth section at the bottom of this page for more.
    #
    # Django unicorn acts as a frontend framework for making dyanmic webpages
    # (i.e. AJAX calls can be made to update the views)
    # "django_unicorn",
    "simmate.website.configs.UnicornConfig",  # fork of django_unicorn
    #
    # Django simple history lets you track history of changes (and who made
    # those changes) for a given model. This is important for models that users
    # interact with and edit in the UI
    "simple_history",
    #
    # Other third-party apps/tools to consider. Note that some of these don't
    # need to be installed apps while some also request different setups.
    #   django-ratelimit
    #   dj-stripe
    #   django-graphene (+ GraphQL)
    #   django-redis
    #
    # These third-party tools are only to help with development and we should
    # try to avoid adding these as installed apps by default.
    #   "django_extensions",  # for development tools
    #   "debug_toolbar",  # django-debug-toolbar  # for debuging and profile-time info
    #
    # Any extra apps from the user (such as django-table2 or some other package)
    *settings.extra_django_apps,
    # Simmate apps + user apps
    "simmate.website.configs.CoreComponentsConfig",
    "simmate.website.configs.DataExplorerConfig",
    "simmate.website.configs.WorkflowsConfig",
    *settings.apps,
]
# OPTIMIZE: for now, I just load everything, but I will want to allow users to
# to disable some apps from loading. This will allow faster import/setup times
# when running small scripts. One idea is to have an applications_override.yaml
# where the user specifies only what they want. Alternatively, I can use
# a general DATABASE_ONLY keyword or something similar to limit what's loaded.

# --------------------------------------------------------------------------------------

# EMAIL SETTINGS
EMAIL_BACKEND = settings.website.email.backend
EMAIL_HOST = settings.website.email.host
EMAIL_PORT = settings.website.email.port
EMAIL_USE_TLS = settings.website.email.use_tls
EMAIL_HOST_USER = settings.website.email.host_user
EMAIL_HOST_PASSWORD = settings.website.email.host_password
DEFAULT_FROM_EMAIL = settings.website.email.from_email
EMAIL_SUBJECT_PREFIX = settings.website.email.subject_prefix
EMAIL_TIMEOUT = settings.website.email.timeout
ADMINS = settings.website.admins

# --------------------------------------------------------------------------------------

# This sets the default field for primary keys in django models
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # This is for tracking WHO changes a model (attaches User)
    "simple_history.middleware.HistoryRequestMiddleware",
    # adds specific authentication methods, such as login by email
    "allauth.account.middleware.AccountMiddleware",
    # add token-based authentication for programmatic access (e.g, REST API)
    "simmate.website.core_components.middleware.TokenAuthenticationMiddleware",
    # tracks page visits accross the website
    "simmate.website.core_components.middleware.WebsitePageVisitMiddleware",
    # Note: extras such as RequireLoginMiddleware are added conditionally below
]

# "core" here is based on the name of my main django folder
ROOT_URLCONF = "simmate.website.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            settings.config_directory / "templates",  # let's user easily override html
            # note: this dir is automatically picked up because it's within an
            # app, but we need it to come BEFORE some other apps (such as allauth)
            # in order to properly override default templates.
            settings.django_directory / "core_components" / "templates",
            # Then APP_DIRS are checked in order
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # We have custom template tags that should be loaded by default.
            # This avoids us having to do {% load simmate_ui_tags %} in
            # a bunch of templates.
            "builtins": [
                "django.contrib.humanize.templatetags.humanize",
                "simmate.website.core_components.templatetags.simmate_input_forms",
                "simmate.website.core_components.templatetags.simmate_settings",
                "simmate.website.core_components.templatetags.simmate_utils",
                "simmate.website.unicorn.templatetags.unicorn",
            ],
        },
    },
]

# "core" here is based on the name of my main django folder
WSGI_APPLICATION = "simmate.website.core.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

DATETIME_INPUT_FORMATS = [
    "%Y-%m-%dT%H:%M",  # this is a custom format I added to get my form widgets working.
    "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
    "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%Y-%m-%d",  # '2006-10-25'
    "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
    "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
    "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y %H:%M:%S",  # '10/25/06 14:30:59'
    "%m/%d/%y %H:%M:%S.%f",  # '10/25/06 14:30:59.000200'
    "%m/%d/%y %H:%M",  # '10/25/06 14:30'
    "%m/%d/%y",  # '10/25/06'
]

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
# !!! Consider removing in the future.
USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
# collect by running 'python manage.py collectstatic'
STATIC_URL = "/static/"
STATIC_ROOT = settings.django_directory / "static"

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    get_directory(
        settings.config_directory / "static_files"
    ),  # let's user add their own files
]

# Ensures users' caches are reset in production when a static file's content changes.
# Note however that this requires 'collectstatic' to be ran before 'runserver'
# when DEBUG=False -- otherwise the server will error.
if settings.website.static_file_hashes:
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )

# For the dynamically-created structure files, we need to include the static
# directory this to work during local testing. This is NOT allowed in a
# production server, so we don't include it when DEBUG is set to False.
# if DEBUG:
#     STATICFILES_DIRS += [STATIC_ROOT]

# Allows the use of iFrames from within Simmate (such as the structure-viewer)
X_FRAME_OPTIONS = "SAMEORIGIN"

# -----------------------------------------------------------------------------

# Extra settings for django-allauth

# Note: these backends are for session-based auth. API Token auth is separate
# and carried out via a separate middleware.
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

# TODO:
# Set how long a user can stay signed-in for. When this cookie expires, the
# user will be signed-out and asked to authenticate again. Django's default
# is 1209600 (2 weeks, in seconds).
# SESSION_COOKIE_AGE = 86400 # 24hrs, in seconds

# simple setting required by allauth. This is intended for hosting several
# websites that all use the same django backend for account sign-in, which
# is not the case for simmate -- so we default to 1 (the main site)
SITE_ID = 1

# We start with the providers as an empty dictionary and only fill them
# if client_id and secrets are supplied in as env variables. We do this
# because we don't want broken links when users first start their server.
SOCIALACCOUNT_PROVIDERS = {}
# Other authentication plugins to consider
# "allauth.socialaccount.providers.digitalocean"
# "allauth.socialaccount.providers.orcid"

_oauth = settings.website.social_oauth

# Sign-in via Google accounts
if _oauth.google.client_id and _oauth.google.secret:
    INSTALLED_APPS.append("allauth.socialaccount.providers.google")
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APP": {
            "client_id": _oauth.google.client_id,
            "secret": _oauth.google.secret,
        },
    }

# Sign-in via Github accounts
if _oauth.github.client_id and _oauth.github.secret:
    INSTALLED_APPS.append("allauth.socialaccount.providers.github")
    SOCIALACCOUNT_PROVIDERS["github"] = {
        "APP": {
            "client_id": _oauth.github.client_id,
            "secret": _oauth.github.secret,
        },
    }

# Sign-in via Microsoft accounts
if _oauth.microsoft.client_id and _oauth.microsoft.secret:
    INSTALLED_APPS.append("allauth.socialaccount.providers.microsoft")
    SOCIALACCOUNT_PROVIDERS["microsoft"] = {
        "APP": {
            "client_id": _oauth.microsoft.client_id,
            "secret": _oauth.microsoft.secret,
            "key": "",
        },
        "TENANT": "organizations",  # limits to internal use
    }

# Initiate social login immediately -- rather than jumping to a separate
# page and then posting.
SOCIALACCOUNT_LOGIN_ON_GET = True
# SECURITY: consider removing per django-allauth's recommendation

# options for login/logoff views
LOGIN_REDIRECT_URL = "/accounts/profile/"  # this is already the default
LOGOUT_REDIRECT_URL = "/accounts/loginstatus/"

# By default, we turn off email verification. If you wish, you can switch
# this to "optional" or "mandatory"
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "none")

# -----------------------------------------------------------------------------

# Many auth endpoints require a https instead of http response:
#   https://stackoverflow.com/questions/67726070/
# We only use this in production
if not settings.website.debug:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

if settings.website.require_login:
    MIDDLEWARE.append(
        "simmate.website.core_components.middleware.RequireLoginMiddleware"
    )

LOGIN_REQUIRED_URLS = (r"/(.*)$",)
LOGIN_REQUIRED_URLS_EXCEPTIONS = (
    r"/accounts(.*)$",
    r"/admin(.*)$",
    r"/static(.*)$",
    *settings.website.require_login_exceptions,
)

# -----------------------------------------------------------------------------

# BUG: To use Django ORM within IPython, Spyder, and Jupyter notebooks, which
# are examples of async consoles, I need to allow unsafe.
# Read more at...
# https://docs.djangoproject.com/en/5.0/topics/async/#async-safety
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# -----------------------------------------------------------------------------

# For advanced users, we let them override Django settings directly.
# But by default, nothing is changed.
locals().update(settings.django_settings)

# To print out all SQL queries. Also consider switching to use Silk:
#   https://github.com/jazzband/django-silk
# https://stackoverflow.com/questions/4375784/how-to-log-all-sql-queries-in-django
if settings.website.log_sql:
    LOGGING = {
        "version": 1,
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "filters": ["require_debug_true"],
                "class": "logging.StreamHandler",
            }
        },
        "loggers": {
            "django.db.backends": {
                "level": "DEBUG",
                "handlers": ["console"],
            }
        },
    }
