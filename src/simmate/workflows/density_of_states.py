# -*- coding: utf-8 -*-

"""
Calculate and plot the density of states (DOS) for a given crystal structure
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:

from simmate.calculators.vasp.workflows.density_of_states import (
    workflow as matproj_workflow,
)
