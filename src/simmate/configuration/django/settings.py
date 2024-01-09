"""
Defines all Django settings for Simmate.

Note, some settings are dynamically determined, such as the installed apps and
database backend being used.
"""

import os

from simmate.configuration import settings
from simmate.utilities import get_directory

# --------------------------------------------------------------------------------------

# DATABASE CONNECTION
DATABASES = {"default": settings.database}

# List all applications that Django will initialize with. Write the full python
# path to the app or it's config file. Note that relative python paths work too
# if you are developing a new app.
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
    #
    # Simmate apps + user apps
    *settings.apps,
]
# OPTIMIZE: for now, I just load everything, but I will want to allow users to
# to disable some apps from loading. This will allow faster import/setup times
# when running small scripts. One idea is to have an applications_override.yaml
# where the user specifies only what they want. Alternatively, I can use
# a general DATABASE_ONLY keyword or something similar to limit what's loaded.

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
            settings.config_directory / "templates",  # let's user easily override html
            settings.django_directory / "templates",  # a single templates folder
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
STATIC_ROOT = settings.django_directory / "static"

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    get_directory(
        settings.config_directory / "static_files"
    ),  # let's user add their own files
    settings.django_directory / "static_files",
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
# https://docs.djangoproject.com/en/5.0/topics/async/#async-safety
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
