# -*- coding: utf-8 -*-

from . import settings  # configures settings but has no functionality
from .client import get_dask_client
from .submit import batch_submit
