# -*- coding: utf-8 -*-

"""
This settings file is only for running Simmate's test suite with pytest.

It contain's a little "hack" so devs don't have to manually edit their django
settings. This hack simply adds `simmate.website.test_app` to our INSTALLED_APPS
setting. The test app is required for testing abstract models as it creates some
test tables for us -- ones that we don't want outside of pytest.
"""

# I don't want to list out all the settings used in the other file, but still
# need all of them imported an environment variable here. So I use this
# shortcut
from .settings import *

# of all the settings we just imported, we only need to update the installed apps
INSTALLED_APPS.append("simmate.website.test_app.apps.TestAppConfig")
