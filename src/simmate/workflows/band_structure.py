# -*- coding: utf-8 -*-

"""
Calculate and plot the band structure for a given crystal structure
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:

from simmate.calculators.vasp.workflows.band_structure import (
    workflow as matproj_workflow,
)
