# -*- coding: utf-8 -*-

# This file sets up a shortcut for importing so that you can do...
#   from simmate.calculators.vasp.error_handlers.all import TetrahedronMesh, Eddrmm, ...
# instead of what's written below. You should only use this shortcut if you are
# using ALL of the classes below or if you are running some quick interactive test.

from simmate.calculators.vasp.error_handlers.tetrahedron_mesh import TetrahedronMesh
from simmate.calculators.vasp.error_handlers.eddrmm import Eddrmm
from simmate.calculators.vasp.error_handlers.incorrect_smearing import (
    IncorrectSmearingHandler,
)
from simmate.calculators.vasp.error_handlers.mesh_symmetry import (
    MeshSymmetryErrorHandler,
)
from simmate.calculators.vasp.error_handlers.unconverged import UnconvergedErrorHandler
from simmate.calculators.vasp.error_handlers.nonconverging import (
    NonConvergingErrorHandler,
)
from simmate.calculators.vasp.error_handlers.potim import PotimErrorHandler
from simmate.calculators.vasp.error_handlers.positive_energy import (
    PositiveEnergyErrorHandler,
)
from simmate.calculators.vasp.error_handlers.frozen import FrozenErrorHandler
from simmate.calculators.vasp.error_handlers.large_sigma import LargeSigmaErrorHandler
