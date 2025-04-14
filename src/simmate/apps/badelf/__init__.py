# -*- coding: utf-8 -*-
try:
    import pybader
except:
    raise Exception(
        "Missing app-specific dependencies. Make sure to read our installation guide."
        "The `badelf` app requires two additional dependencies: `pybader` and `networkx`."
        "Install these with `conda install -c conda-forge pybader networkx`"
    )
