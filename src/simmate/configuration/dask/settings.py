# -*- coding: utf-8 -*-

import os
from pathlib import Path


def load_cluster_settings() -> dict:
    """
    Load our default cluster type and worker settings. This is loaded
    from the file `dask_cluster.yaml`.

    Note, module must be imported BEFORE we import any dask modules.
    """

    SIMMATE_DIRECTORY = Path.home() / "simmate"
    CLUSTER_YAML = SIMMATE_DIRECTORY / "dask_cluster.yaml"
    if CLUSTER_YAML.exists():
        os.environ.setdefault(
            "DASK_CONFIG",
            SIMMATE_DIRECTORY / "dask_cluster.yaml",
        )


# Automatically call the method above when importing this module
load_cluster_settings()
