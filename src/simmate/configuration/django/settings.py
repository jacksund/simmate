"""
Defines all Django settings for Simmate.

Note, some settings are dynamically determined, such as the installed apps and
database backend being used.
"""

import os
from pathlib import Path

import dj_database_url  # needed for DigitalOcean database connection
import yaml

from simmate import website  # needed to specify location of built-in apps
from simmate.utilities import get_conda_env, get_directory

# --------------------------------------------------------------------------------------

# SET MAIN DIRECTORIES

# We check for extra django apps in the user's home directory and in a "hidden"
# folder named "simmate/extra_applications".
# For windows, this would be something like...
#   C:\Users\exampleuser\simmate\extra_applications
# Note, we use get_directory in order to create that folder if it does not exist.
SIMMATE_DIRECTORY = get_directory(Path.home() / "simmate")

# This directory is where simmate.website is located and helps us indicate
# where things like our templates or static files are located. We find this
# by looking at the import path to see where python installed it.
DJANGO_DIRECTORY = Path(website.__file__).absolute().parent

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
DEBUG = os.getenv("DEBUG", "False") == "True"

# To make this compatible with DigitalOcean, we try to grab the allowed hosts
# from an enviornment variable, which we then split into a list. If this
# enviornment variable isn't set yet, then we just defaul to the localhost.
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# BUG-FIX: Django-unicorn ajax requests sometimes come from the server-side
# ingress (url for k8s) or a nginx load balancer. To get past a 403 forbidden
# result, we need to sometimes specify allowed origins.
CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost",
).split(",")

# This is for setting the database via an connection URL. This is done as
# an environment variable to allow setup with DigitalOcean
DATABASE_URL = os.getenv("DATABASE_URL", None)
# this is not a typical Django setting

# Keep the secret key used in production secret!
# For DigitalOcean, we grab this secret key from an enviornment variable.
# If this variable isn't set, then we instead generate a random one.
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "pocj6cunub4zi31r02vr5*5a2c(+_a0+(zsswa7fmus^o78v)r"
)
# !!! I removed get_random_secret_key() so I don't have to sign out every time
# while testing my server. I may change this back in the future.
# from django.core.management.utils import get_random_secret_key

# Sometimes we lock down the website to registered/approved users.
# By default, we allow anonymous users to explore because this makes things like
# REST API calls much easier for them. In special cases, such as industry, we
# ONLY let users sign in via a specific allauth endpoint. An example of this
# is Corteva limiting users to those approved via their Microsoft auth.
REQUIRE_LOGIN = os.getenv("REQUIRE_LOGIN", "False") == "True"
# when setting REQUIRE_INTERNAL_LOGIN, set it to the allauth provider type
# (such as "microsoft")
REQUIRE_LOGIN_INTERNAL = os.getenv("REQUIRE_LOGIN_INTERNAL", "False")
if REQUIRE_LOGIN_INTERNAL == "False":
    REQUIRE_LOGIN_INTERNAL = False
else:
    assert REQUIRE_LOGIN_INTERNAL in ["microsoft", "google"]
    REQUIRE_LOGIN = True
# example: r'/apps/spotfire(.*)$'
REQUIRE_LOGIN_EXCEPTIONS = [
    e for e in os.getenv("REQUIRE_LOGIN_EXCEPTIONS", "").split(";") if e
]
LOGIN_MESSAGE = os.getenv("LOGIN_MESSAGE", "")

# These allow server maintainers to override the homepage and profile views, which
# is important if they involve loading custom apps/models for their templates.
PROFILE_VIEW = os.getenv("PROFILE_VIEW", None)
HOME_VIEW = os.getenv("HOME_VIEW", None)

# --------------------------------------------------------------------------------------

# DATBASE CONNECTION

# Normally in Django, you can set the database like so: (using Postgres)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "simmate-database-pool",  # default on DigitalOcean is defaultdb
#         "USER": "doadmin",
#         "PASSWORD": "dibi5n3varep5ad8",
#         "HOST": "db-postgresql-nyc3-09114-do-user-8843535-0.b.db.ondigitalocean.com",
#         "PORT": 25061,
#         "OPTIONS": {"sslmode": "require"},
#         # "CONN_MAX_AGE": 0,  # set this to higher value for production website server
#     }
# }
# But this section instead determines the database through a series of checks.

# There are three types of database files that we check for -- in order of priority:
#   1. database.yaml
#   2. my_env-database.yaml
#   3. use a DATABASE_URL env variable
#   4. my_env-database.sqlite3 <-- and create this if doesn't exist
DATABASE_YAML = SIMMATE_DIRECTORY / "database.yaml"
CONDA_DATABASE_YAML = SIMMATE_DIRECTORY / f"{CONDA_ENV}-database.yaml"
CONDA_DATABASE_SQLITE3 = SIMMATE_DIRECTORY / f"{CONDA_ENV}-database.sqlite3".strip("-")
# if the user is in the (base) env or not using conda, then we will have a
# value of "-database.sqlite3". We remove the starting "-" here.


# Our 1st priority is checking for a "simmate/database.yaml" file
if DATABASE_YAML.exists():
    with DATABASE_YAML.open() as file:
        DATABASES = yaml.full_load(file)

# Our 2nd priority is checking for a file like "/simmate/my_env-database.yaml
elif CONDA_DATABASE_YAML.exists():
    with CONDA_DATABASE_YAML.open() as file:
        DATABASES = yaml.full_load(file)


# Our 3rd prioirity is Digital Ocean setup or ENV variable. The connection
# parameters were set as an env variable named DATABASE_URL.
elif DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL),
    }

# Our final prioirity is a local sqlite database name "my_env-database.sqlite3".
# This is the default setting used when simmate is first installed.
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": CONDA_DATABASE_SQLITE3,
        }
    }

# As an extra, we keep a DATABASE_BACKEND variable for backend-specific methods
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASE_BACKEND = "sqlite3"
elif DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASE_BACKEND = "postgresql"
else:
    DATABASE_BACKEND = "unknown"

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
    "simmate.website.configs.CoreComponentsConfig",
    "simmate.website.configs.DataExplorerConfig",
    "simmate.website.configs.WorkflowsConfig",
    "simmate.website.configs.WorkflowEngineConfig",
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
    # These are apps created by third-parties that give us extra features
    "crispy_forms",  # django-crispy-forms for HTML boostrap forms
    "rest_framework",  # djangorestframework for the REST API
    "django_filters",  # django-filter for filterable REST API urls
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
    "django_unicorn",
    #
    # Django simple history lets you track history of changes (and who made
    # those changes) for a given model. This is important for models that users
    # interact with and edit in the UI
    "simple_history",
    #
    # Django contrib comments let you track comments on a model and handles
    # moderation / user / date features for you.
    "django_comments",
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
]

# We also check if the user has a "apps.yaml" file. In this file, the
# user can provide extra apps to install for Django. We simply append these
# to our list above. By default we include apps that are packaged with simmate,
# such as the VASP workflows app.
DEFAULT_SIMMATE_APPS = [
    "simmate.workflows.configs.BaseWorkflowsConfig",
    "simmate.apps.configs.QuantumEspressoConfig",
    "simmate.apps.configs.VaspConfig",
    "simmate.apps.configs.BaderConfig",
    "simmate.apps.configs.EvolutionConfig",
    "simmate.apps.configs.MaterialsProjectConfig",
    # These apps may become defaults in the future:
    # "simmate.apps.configs.BadelfConfig",
    # "simmate.apps.configs.CleaseConfig",
    # "simmate.apps.configs.WarrenLabConfig",
]
APPLICATIONS_YAML = SIMMATE_DIRECTORY / f"{CONDA_ENV}-apps.yaml"
# create the file if it doesn't exist yet
if not APPLICATIONS_YAML.exists():
    with APPLICATIONS_YAML.open("w") as file:
        content = yaml.dump(DEFAULT_SIMMATE_APPS)
        file.write(content)

# load apps that the user wants installed
with APPLICATIONS_YAML.open() as file:
    SIMMATE_APPS = yaml.full_load(file)
    # We only load extra apps if the file isn't empty
    if SIMMATE_APPS:
        # now add each app to our list above so Django loads it.
        for app in SIMMATE_APPS:
            INSTALLED_APPS.append(app)
    else:
        SIMMATE_APPS = []

# --------------------------------------------------------------------------------------

# DATBASE EXPLORER

# We also check if the user has a "apps.yaml" file. In this file, the
# user can provide extra apps to install for Django. We simply append these
# to our list above. By default we include apps that are packaged with simmate,
# such as the VASP workflows app.
DEFAULT_SIMMATE_DATA = [
    "simmate.database.third_parties.AflowPrototype",
    # "simmate.database.third_parties.AflowStructure",  # Not allowed yet
    "simmate.database.third_parties.CodStructure",
    "simmate.database.third_parties.JarvisStructure",
    "simmate.database.third_parties.MatprojStructure",
    "simmate.database.third_parties.OqmdStructure",
]
DATA_EXPLORER_YAML = SIMMATE_DIRECTORY / f"{CONDA_ENV}-data.yaml"
# create the file if it doesn't exist yet
if not DATA_EXPLORER_YAML.exists():
    with DATA_EXPLORER_YAML.open("w") as file:
        content = yaml.dump(DEFAULT_SIMMATE_DATA)
        file.write(content)

# load apps that the user wants installed
with DATA_EXPLORER_YAML.open() as file:
    SIMMATE_DATA = yaml.full_load(file)
    # If the file is empty, just keep our result as an empty list
    if not SIMMATE_DATA:
        SIMMATE_DATA = []

# --------------------------------------------------------------------------------------

# EMAILS

# Settings for sending automated emails.
# For example, this can be set up for GMail by...
#   1. enabling IMAP (in gmail settings)
#   2. Having 2-factor auth turned on
#   3. Adding an App Password (in account settings)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # this is the default
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")  # or outlook.office365.com
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", False) == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_FROM", "simmate.team@gmail.com")
EMAIL_SUBJECT_PREFIX = "[Simmate] "
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", 5))

# These people get an email when DEBUG=False
ADMINS = [
    ("jacksund", "jacksundberg123@gmail.com"),
    ("jacksund-corteva", "jack.sundberg@corteva.com"),
]

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
]

# "core" here is based on the name of my main django folder
ROOT_URLCONF = "simmate.website.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            SIMMATE_DIRECTORY / "templates",  # let's user easily override html
            DJANGO_DIRECTORY / "templates",  # a single templates folder
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
STATIC_ROOT = DJANGO_DIRECTORY / "static"

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    get_directory(SIMMATE_DIRECTORY / "static_files"),  # let's user add their own files
    DJANGO_DIRECTORY / "static_files",
]


# For the dynamically-created structure files, we need to include the static
# directory this to work during local testing. This is NOT allowed in a
# production server, so we don't include it when DEBUG is set to False.
# if DEBUG:
#     STATICFILES_DIRS += [STATIC_ROOT]

# This sets the django-crispy formating style
CRISPY_TEMPLATE_PACK = "bootstrap4"

# These settings help configure djangorestframework and our REST API
REST_FRAMEWORK = {
    # The REST framework has both authentication AND permission classes. Adding
    # the auth classes ensure we have user data available when rendering the
    # template. Then I allow anyone (anonymous and signed in users) to access
    # the REST APIs. Note, even though this is allow-all, we still have the
    # "RequireLoginMiddleware" applied elsewhere if the admin choses.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Because we have a massive number of results for different endpoints,
    # we want to set results to be paginated by 20 results per page. This
    # way we don't have to set a page limit for every individual endpoint. Note
    # I can consider switching to LimitOffsetPagination in the future, which
    # allows the number of results per page to vary, but I don't do this
    # for now because there's no easy way to set paginator.max_limit in the
    # settings here.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
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

# Sign-in via Microsoft accounts
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", None)
MICROSOFT_SECRET = os.getenv("MICROSOFT_SECRET", None)
if MICROSOFT_CLIENT_ID and MICROSOFT_SECRET:
    INSTALLED_APPS.append("allauth.socialaccount.providers.microsoft")
    SOCIALACCOUNT_PROVIDERS["microsoft"] = {
        "APP": {
            "client_id": MICROSOFT_CLIENT_ID,
            "secret": MICROSOFT_SECRET,
            "key": "",
        },
        "TENANT": "organizations",  # limits to internal use
    }

# Initiate social login immediately -- rather than jumping to a separate
# page and then posting.
# SECURITY: consider removing per django-allauth's recommendation
SOCIALACCOUNT_LOGIN_ON_GET = True

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
if not DEBUG:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

if REQUIRE_LOGIN:
    MIDDLEWARE.append("simmate.website.require_login.RequireLoginMiddleware")

LOGIN_REQUIRED_URLS = (r"/(.*)$",)
LOGIN_REQUIRED_URLS_EXCEPTIONS = (
    r"/accounts(.*)$",
    r"/admin(.*)$",
    r"/static(.*)$",
    *REQUIRE_LOGIN_EXCEPTIONS,
)

# -----------------------------------------------------------------------------

# BUG: To use Django ORM within IPython, Spyder, and Jupyter notebooks, which
# are examples of async consoles, I need to allow unsafe.
# Read more at...
# https://docs.djangoproject.com/en/4.0/topics/async/#async-safety
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
