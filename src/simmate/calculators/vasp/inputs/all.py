# -*- coding: utf-8 -*-

# This file sets up a shortcut for importing so that you can do...
#   from simmate.calculators.vasp.inputs.all import Incar, Poscar, Kpoints, Potcar
# instead of what's written below. You should only use this shortcut if you are
# using ALL of the classes below or if you are running some quick interactive test.

from simmate.calculators.vasp.inputs.incar import Incar
from simmate.calculators.vasp.inputs.kpoints import Kpoints
from simmate.calculators.vasp.inputs.potcar import Potcar
from simmate.calculators.vasp.inputs.poscar import Poscar
