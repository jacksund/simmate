# -*- coding: utf-8 -*-

# CLEASE is an optional dependency, so make sure it's installed before loading
# this module
try:
    import clease
except:
    raise ModuleNotFoundError(
        "The Simmate-Clease app requires CLEASE to run. Please install CLEASE to "
        "your python environment with... \n"
        "'conda install -n my_env -c conda-forge clease'"
    )
