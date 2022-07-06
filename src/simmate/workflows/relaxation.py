# -*- coding: utf-8 -*-

"""
Workflows for relaxing a crystal structure
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.relaxation.all import (
    Relaxation__VASP__MatProj,
    Relaxation__VASP__MIT,
    Relaxation__VASP__NEB_Endpoint,
    Relaxation__VASP__Quality00,
    Relaxation__VASP__Quality01,
    Relaxation__VASP__Quality02,
    Relaxation__VASP__Quality03,
    Relaxation__VASP__Quality04,
)
