# -*- coding: utf-8 -*-

# This file sets up a shortcut for importing so that you can do...
#   from simmate.workflows.relaxation.all import mit_relaxation, mp_relaxation, ...
# instead of what's written below. You should only use this shortcut if you are
# using ALL of the classes below or if you are running some quick interactive test.


# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.relaxation.all import (
    relaxation_mit,
    relaxation_quality00,
    relaxation_quality01,
    relaxation_quality02,
    relaxation_quality03,
    relaxation_quality04,
    relaxation_staged,
)
