# -*- coding: utf-8 -*-

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.relaxation import (
    mit_workflow,
    matproj_workflow,
    quality00_workflow,
    quality01_workflow,
    quality02_workflow,
    quality03_workflow,
    quality04_workflow,
    staged_workflow,
    neb_endpoint_workflow,
)
