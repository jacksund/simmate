# -*- coding: utf-8 -*-
try:
    import baderkit
except:
    raise Exception(
        "Missing app-specific dependencies. Make sure to read our installation guide."
        "The `badelf` app requires an additional dependency: `baderkit`."
        "Install these with `conda install -c conda-forge baderkit`"
    )
