# -*- coding: utf-8 -*-

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.population_analysis import (
    bader_matproj_workflow,
    elf_matproj_workflow,
)
