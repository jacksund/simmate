"""
Defines all Django settings for Simmate.

Note, some settings are dynamically determined, such as the installed apps and
database backend being used.
"""

import os
import sys
from pathlib import Path

import yaml

# from django.core.management.utils import get_random_secret_key

import dj_database_url  # needed for DigitalOcean database connection

from simmate import website  # needed to specify location of built-in apps
from simmate.utilities import get_directory, get_conda_env

# --------------------------------------------------------------------------------------

# SET MAIN DIRECTORIES

# We check for extra django apps in the user's home directory and in a "hidden"
# folder named "simmate/extra_applications".
# For windows, this would be something like...
#   C:\Users\exampleuser\simmate\extra_applications
# Note, we use get_directory in order to create that folder if it does not exist.
SIMMATE_DIRECTORY = get_directory(os.path.join(Path.home(), "simmate"))

# This directory is where simmate.website is located and helps us indicate
# where things like our templates or static files are located. We find this
# by looking at the import path to see where python installed it.
DJANGO_DIRECTORY = os.path.dirname(os.path.abspath(website.__file__))

# Some settings below also depend on the conda env name. This makes switching
# between different databases and settings as easy as activating different
# conda environments
CONDA_ENV = get_conda_env()

# --------------------------------------------------------------------------------------

# ENVIORNMENT VARIABLES

# There are a number of settings that we let the user configure via enviornment
# variables, which helps control things when we want to launch a website server.
# We check for these variables in the enviornment, and if they are not set,
# they fall back to a default.

# Don't run with debug turned on in production!
# For DigitalOcean, we try grabbing this from an enviornment variable. If that
# variable isn't set, then we assume we are debugging. The == at the end converts
# the string to a boolean for us.
DEBUG = os.getenv("DEBUG", "True") == "True"

# To make this compatible with DigitalOcean, we try to grab the allowed hosts
# from an enviornment variable, which we then split into a list. If this
# enviornment variable isn't set yet, then we just defaul to the localhost.
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# This decides wether we use a local sqlite database. The order of priority for
# databases goes...
#   (1) Check for a "database.yaml" file in the user's home directory
#   (2) Check for the USE_LOCAL_DATABASE enviornment variable (defaults to True)
#   (3) If USE_LOCAL_DATABASE=False, then check for DATABASE_URL enviornment variable
USE_LOCAL_DATABASE = os.getenv("USE_LOCAL_DATABASE", "True") == "True"
# this is not a typical Django setting

# Keep the secret key used in production secret!
# For DigitalOcean, we grab this secret key from an enviornment variable.
# If this variable isn't set, then we instead generate a random one.
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "pocj6cunub4zi31r02vr5*5a2c(+_a0+(zsswa7fmus^o78v)r"
)
# !!! I removed get_random_secret_key() so I don't have to sign out every time
# while testing my server. I may change this back in the future.

# --------------------------------------------------------------------------------------

# DATBASE CONNECTION

# There are three types of database files that we check for -- in order of priority:
#   1. database.yaml
#   2. my_env-database.yaml
#   3. my_env-database.sqlite3 (if USE_LOCAL_DATABASE=True) <-- and create this if doesn't exist
#   4. use a DATABASE_URL env variable
DATABASE_YAML = os.path.join(SIMMATE_DIRECTORY, "database.yaml")
CONDA_DATABASE_YAML = os.path.join(SIMMATE_DIRECTORY, f"{CONDA_ENV}-database.yaml")
CONDA_DATABASE_SQLITE3 = os.path.join(
    SIMMATE_DIRECTORY, f"{CONDA_ENV}-database.sqlite3"
).strip("-")
# if the user is in the (base) env or not using conda, then we will have a
# value of "-database.sqlite3". We remove the starting "-" here.


# Our 1st priority is checking for a "simmate/database.yaml" file
if os.path.exists(DATABASE_YAML):
    with open(DATABASE_YAML) as file:
        DATABASES = yaml.full_load(file)

# Our 2nd priority is checking for a file like "/simmate/my_env-database.yaml
elif os.path.exists(CONDA_DATABASE_YAML):
    with open(CONDA_DATABASE_YAML) as file:
        DATABASES = yaml.full_load(file)

# This is the default behavior
# Our 3rd prioirity is a local sqlite database name "my_env-database.sqlite3"

elif USE_LOCAL_DATABASE is True:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": CONDA_DATABASE_SQLITE3,
        }
    }

# Lastly, if we make it to this point, we are likely using DigitalOcean and
# running a server. When DigitalOcean runs the "collectstatic" command, we don't
#  want to connect any database. So we use the "sys" library to look at the
# command and ensure it doesn't involve "collectstatic". Otherwise we use the
# URL that is set with our enviornment variable.
elif len(sys.argv) > 0 and sys.argv[1] != "collectstatic":
    # ensure that we have the database URL properly configured in DigitalOcean
    if os.getenv("DATABASE_URL", None) is None:
        raise Exception("DATABASE_URL environment variable not defined")
    # Now connect our DigitalOcean to this database!
    DATABASES = {
        "default": dj_database_url.parse(os.environ.get("DATABASE_URL")),
    }

# Here is an example of connecting to a Postgres server normally...
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql_psycopg2",
#         "NAME": "simmate-database-pool",  # default on DigitalOcean is defaultdb
#         "USER": "doadmin",
#         "PASSWORD": "dibi5n3varep5ad8",
#         "HOST": "db-postgresql-nyc3-09114-do-user-8843535-0.b.db.ondigitalocean.com",
#         "PORT": 25061,
#         "OPTIONS": {"sslmode": "require"},  # !!! is this needed?
#         # "CONN_MAX_AGE": 0,  # set this to higher value for production website server
#     }
# }

# --------------------------------------------------------------------------------------

# INSTALLED APPS

# OPTIMIZE: for now, I just load everything, but I will want to allow users to
# to disable some apps from loading. This will allow faster import/setup times
# when running small scripts. One idea is to have an applications_override.yaml
# where the user specifies only what they want. Alternatively, I can use
# a general DATABASE_ONLY keyword or something similar to limit what's loaded.

# List all applications that Django will initialize with. Write the full python
# path to the app or it's config file. Note that relative python paths work too
# if you are developing a new app. Advanced users can remove unnecessary apps
# if you'd like to speed up django's start-up time.
INSTALLED_APPS = [
    #
    # These are all apps that are built by Simmate
    "simmate.website.core_components.apps.CoreComponentsConfig",
    "simmate.website.third_parties.apps.ThirdPartyConfig",
    "simmate.website.workflows.apps.WorkflowsConfig",
    #
    # These are built-in django apps that we use for extra features
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Other apps installed with Django to consider
    #   "django.contrib.humanize",
    #   "django.contrib.postgres",
    #   "django.contrib.redirects",
    #   "django.contrib.sitemaps",
    #
    # These are apps created by third-parties that give us extra features
    "crispy_forms",  # django-crispy-forms
    "rest_framework",  # djangorestframework
    "django_filters",  # django-filter
    #
    # Apps for django-allauth that allow sign-on using external accounts
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # note: there are extra apps installed based on configuration. See the
    # allauth section at the bottom of this page for more.
    #
    # Other third-party apps/tools to consider. Note that some of these don't
    # need to be installed apps while some also request different setups.
    #   django-ratelimit
    #   dj-stripe
    #   django-unicorn
    #   django-graphene (+ GraphQL)
    #   django-redis
    #
    # These third-party tools are only to help with development and we should
    # try to avoid adding these as installed apps by default.
    #   "django_extensions",  # for development tools
    #   "debug_toolbar",  # django-debug-toolbar  # for debuging and profile-time info
]

# We also check if the user has a "applications.yaml" file. In this file, the
# user can provide extra apps to install for Django. We simply append these
# to our list above
APPLICATIONS_YAML = os.path.join(SIMMATE_DIRECTORY, "applications.yaml")
if os.path.exists(APPLICATIONS_YAML):
    with open(APPLICATIONS_YAML) as file:
        # load the list of extra apps. Since this is really just one line for
        # each, it is loaded as a single string separated by a space.
        extra_apps = yaml.full_load(file).split()
        # now add each app to our list above so Django loads it.
        for app in extra_apps:
            INSTALLED_APPS.append(app)

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
]

# "core" here is based on the name of my main django folder
ROOT_URLCONF = "simmate.website.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # I set DIRS below so I can have a single templates folder
        "DIRS": [os.path.join(DJANGO_DIRECTORY, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
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
        "NAME": (
            "django.contrib.auth."
            "password_validation.UserAttributeSimilarityValidator"
        ),  # formatted in this odd way because of line length limit for Black
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
STATIC_ROOT = os.path.join(DJANGO_DIRECTORY, "static")

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [os.path.join(DJANGO_DIRECTORY, "static_files")]

# For the dynamically-created structure files, we need to include the static
# directory this to work during local testing. This is NOT allowed in a
# production server, so we don't include it when DEBUG is set to False.
if DEBUG:
    STATICFILES_DIRS += [os.path.join(DJANGO_DIRECTORY, "static")]

# This sets the django-crispy formating style
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Settings for sending emails with my gmail account
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # this is the default
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "simmate.team@gmail.com"  # os.environ.get('EMAIL_USER')
# !!! REMOVE IN PRODUCTION. Use this instead: os.environ.get('EMAIL_PASSWORD')
EMAIL_HOST_PASSWORD = "example-password-123"

# These settings help configure djangorestframework and our REST API
REST_FRAMEWORK = {
    # The REST framework has both authentication AND permission classes. By
    # default I allow anything, but may revisit these if the user-base ever grows:
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # Because we have a massive number of results for different endpoints,
    # we want to set results to be paginated by 25 results per page. This
    # way we don't have to set a page limit for every individual endpoint. Note
    # I can consider switching to LimitOffsetPagination in the future, which
    # allows the number of results per page to vary, but I don't do this
    # for now because there's no easy way to set paginator.max_limit in the
    # settings here.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    # To prevent users from querying too much and bringing down our servers,
    # we set a throttle rate on each user. Here, "anon" represents an anonymous
    # user (not signed-in) while signed-in users have access to higher download
    # rates. Note these are very restrictive because we prefer users to download
    # full databases and use Simmate locally instead.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hr"},
    # We use django-filter to automatically handle filtering from a REST url
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    # There are multiple ways to render the data, where we default to a nice HTML
    # view, but also support pure JSON or using Django-REST's interactive API
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.TemplateHTMLRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework.renderers.JSONRenderer",
    ],
}

# Allows the use of iFrames from within Simmate (such as the structure-viewer)
X_FRAME_OPTIONS = "SAMEORIGIN"

# -----------------------------------------------------------------------------

# Extra settings for django-allauth

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

# simple setting required by allauth. not sure what it does...
SITE_ID = 1

# We start with the providers as an empty dictionary and only fill them
# if client_id and secrets are supplied in as env variables. We do this
# because we don't want broken links when users first start their server.
SOCIALACCOUNT_PROVIDERS = {}
# Other authentication plugins to consider
# "allauth.socialaccount.providers.digitalocean"
# "allauth.socialaccount.providers.orcid"

# Sign-in via Google accounts
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", None)
GOOGLE_SECRET = os.getenv("GOOGLE_SECRET", None)
if GOOGLE_CLIENT_ID and GOOGLE_SECRET:
    INSTALLED_APPS.append("allauth.socialaccount.providers.google")
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APP": {"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_SECRET}
    }

# Sign-in via Github accounts
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", None)
GITHUB_SECRET = os.getenv("GITHUB_SECRET", None)
if GITHUB_CLIENT_ID and GITHUB_SECRET:
    INSTALLED_APPS.append("allauth.socialaccount.providers.github")
    SOCIALACCOUNT_PROVIDERS["github"] = {
        "APP": {"client_id": GITHUB_CLIENT_ID, "secret": GITHUB_SECRET}
    }

# Initiate social login immediately -- rather than jumping to a separate
# page and then posting.
# SECURITY: consider removing per django-allauth's recommendation
SOCIALACCOUNT_LOGIN_ON_GET = True

# options for login/logoff views
LOGIN_REDIRECT_URL = "/accounts/profile/"  # this is already the default
LOGOUT_REDIRECT_URL = "/accounts/loginstatus/"

# -----------------------------------------------------------------------------

# BUG: To use Django ORM within IPython, Spyder, and Jupyter notebooks, which
# are examples of async consoles, I need to allow unsafe.
# Read more at...
# https://docs.djangoproject.com/en/4.0/topics/async/#async-safety
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
