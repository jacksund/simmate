# -*- coding: utf-8 -*-

import importlib.metadata

__version__ = importlib.metadata.version("simmate")

from simmate.utilities import get_doc_from_readme, check_if_using_latest_version

__doc__ = get_doc_from_readme(__file__)


# Check if there is a newer Simmate version available, and if the current
# installation is out of date, print a message for the user.
try:
    check_if_using_latest_version()
except:
    print("WARNING: Unable to check if using the latest Simmate version.")
