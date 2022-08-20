# -*- coding: utf-8 -*-

import importlib.metadata
import logging

from rich.logging import RichHandler

__version__ = importlib.metadata.version("simmate")

# Some of these utilities use the __version__ above, so this import must come after
from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)


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
