# -*- coding: utf-8 -*-

# ensure badelf's optional deps are present
try:
    import pybader
    import pyrho
except:
    raise Exception(
        "This app requires two optional dependencies: mp-pyrho and pybader. "
        "Install these with `conda install -c conda-forge mp-pyrho pybader`"
    )
