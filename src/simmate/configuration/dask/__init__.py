# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

import os

from . import settings  # configures settings but has no functionality
from .client import get_dask_client
from .submit import batch_submit
