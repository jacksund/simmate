# -*- coding: utf-8 -*-

"""
Workflows for predicting oxidation states within a material
"""

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.population_analysis import (
    bader_matproj_workflow,
    elf_matproj_workflow,
    badelf_matproj_workflow,
    prebader_matproj_workflow,
    prebadelf_matproj_workflow,
)
