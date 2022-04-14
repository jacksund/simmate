# -*- coding: utf-8 -*-

import os
from pathlib import Path


def load_cluster_settings() -> dict:
    """
    Load our default cluster type and worker settings. This is loaded
    from the file `dask_cluster.yaml`.

    Note, module must be imported BEFORE we import any dask modules.
    """

    SIMMATE_DIRECTORY = os.path.join(Path.home(), "simmate")
    CLUSTER_YAML = os.path.join(SIMMATE_DIRECTORY, "dask_cluster.yaml")
    if os.path.exists(CLUSTER_YAML):
        os.environ.setdefault(
            "DASK_CONFIG",
            os.path.join(os.path.expanduser("~"), "simmate", "dask_cluster.yaml"),
        )


# Automatically call the method above when importing this module
load_cluster_settings()
