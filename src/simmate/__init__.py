# -*- coding: utf-8 -*-

# This line just disables anything var from being set as an attribute to the
# simmate module (e.g., it disables `from simmate import RichHandler`)
__all__ = []

try:
    # because we now only support conda-install, do a quick check for our primary
    # 3 dependencies. If any are missing, it is likely the user installed via
    # pip where we didnt list *any* of our dependencies
    import django
    import pymatgen
    import rdkit
except:
    raise Exception(
        "Simmate's core dependencies were not found. "
        "You most likely are seeing this message if you improperly installed simmate "
        "using `pip` or `uv`. "
        "To fix this, make sure you install simmate using conda and in a clean env. "
        "We only support `conda` installs because some of our dependencies "
        "(such as rdkit) only consistently work when installed via conda-forge. "
        "We hope this will change in the future and we're sorry for "
        "the inconvenience!"
    )


import importlib.metadata
import logging

from rich.logging import RichHandler

__version__ = importlib.metadata.version("simmate")

# Configure our logger to output timestamps and "SIMMATE" with logs
# Also changes the logging level to info
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RichHandler(
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
    ],
)
