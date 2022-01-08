# -*- coding: utf-8 -*-

import os

# First we need to load the default configuration for Dask. This is located
# in the simmate configuration directory under the name dask_cluster.yaml.
# This needs to be done BEFORE we import any dask modules, which is why this is
# in the init.
os.environ.setdefault(
    "DASK_CONFIG",
    os.path.join(os.path.expanduser("~"), "simmate", "dask_cluster.yaml"),
)
# TODO: I need to update this to allow for other directories
