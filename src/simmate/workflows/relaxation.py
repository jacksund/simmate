# -*- coding: utf-8 -*-

"""
Workflows for relaxing a crystal structure
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.Vasp" in installed_apps:
from simmate.calculators.vasp.workflows.relaxation.all import (
    Relaxation__Vasp__Matproj,
    Relaxation__Vasp__Mit,
    Relaxation__Vasp__NebEndpoint,
    Relaxation__Vasp__Quality00,
    Relaxation__Vasp__Quality01,
    Relaxation__Vasp__Quality02,
    Relaxation__Vasp__Quality03,
    Relaxation__Vasp__Quality04,
    Relaxation__Vasp__Staged,
)
