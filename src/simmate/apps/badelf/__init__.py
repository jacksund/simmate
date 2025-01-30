# -*- coding: utf-8 -*-
try:
    from pybader.interface import Bader
except:
    raise Exception(
        "The BadELF app requires an additional dependency: the pybader package."
        "Install this with `conda install -c conda-forge pybader`"
    )
