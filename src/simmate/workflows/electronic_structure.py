# -*- coding: utf-8 -*-

"""
Calculate and plot both the density of states (DOS) and band structure
for a given crystal structure
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:

from simmate.calculators.vasp.workflows.electronic_structure.all import (
    ElectronicStructure__Vasp__MatprojFull,
)
