# -*- coding: utf-8 -*-

"""
Workflows for calculating the energy of material
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.static_energy.all import (
    StaticEnergy__Vasp__Matproj,
    StaticEnergy__Vasp__Mit,
    StaticEnergy__Vasp__Quality04,
    StaticEnergy__Vasp__NebEndpoint,
)
