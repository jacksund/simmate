# -*- coding: utf-8 -*-

"""
Workflows for running molecular dynamics simmulations
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:

from simmate.calculators.vasp.workflows.dynamics.all import (
    Dynamics__Vasp__Matproj,
    Dynamics__Vasp__Mit,
    Dynamics__Vasp__MvlNpt,
)
