# -*- coding: utf-8 -*-

import logging
import importlib.metadata


__version__ = importlib.metadata.version("simmate")

# Some of these utilities use the __version__ above, so this import must come after
from simmate.utilities import get_doc_from_readme, check_if_using_latest_version

__doc__ = get_doc_from_readme(__file__)


# Configure our logger to output timestamps and "SIMMATE" with logs
# Also changes the logging level to info
logging.basicConfig(
    format="[SIMMATE-%(levelname)-s %(asctime)-s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


# Check if there is a newer Simmate version available, and if the current
# installation is out of date, print a message for the user.
try:
    check_if_using_latest_version()
except:
    logging.warning("Unable to check if using the latest Simmate version.")
