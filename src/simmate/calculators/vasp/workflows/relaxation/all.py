# -*- coding: utf-8 -*-

# This file sets up a shortcut for importing so that you can do...
#   from simmate.workflows.relaxation.all import mit_relaxation, mp_relaxation, ...
# instead of what's written below. You should only use this shortcut if you are
# using ALL of the classes below or if you are running some quick interactive test.

from simmate.calculators.vasp.workflows.relaxation.mit import workflow as relaxation_mit
from simmate.calculators.vasp.workflows.relaxation.quality_00 import workflow as relaxation_quality00
from simmate.calculators.vasp.workflows.relaxation.quality_01 import workflow as relaxation_quality01
from simmate.calculators.vasp.workflows.relaxation.quality_02 import workflow as relaxation_quality02
from simmate.calculators.vasp.workflows.relaxation.quality_03 import workflow as relaxation_quality03
from simmate.calculators.vasp.workflows.relaxation.quality_04 import workflow as relaxation_quality04
from simmate.calculators.vasp.workflows.relaxation.staged import workflow as relaxation_staged
