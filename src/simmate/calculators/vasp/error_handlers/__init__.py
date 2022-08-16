# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

from .brions import Brions
from .brmix import Brmix
from .edddav import Edddav
from .eddrmm import Eddrmm
from .edwav import Edwav
from .elf_kpar import ElfKpar
from .frozen import Frozen
from .incorrect_shift import IncorrectShift
from .incorrect_smearing import IncorrectSmearing
from .insufficient_bands import InsufficientBands
from .large_sigma import LargeSigma
from .long_vector import LongVector
from .mesh_symmetry import MeshSymmetry
from .nonconverging import NonConverging
from .point_group import PointGroup
from .positive_energy import PositiveEnergy
from .posmap import Posmap
from .potim import Potim
from .pricel import Pricel
from .pssyevx import Pssyevx
from .real_optlay import RealOptlay
from .rhosyg import Rhosyg
from .rotation_matrix import RotationMatrix
from .rotation_matrix_nonint import RotationNonIntMatrix
from .subspace_matrix import SubspaceMatrix
from .symprec_noise import SymprecNoise
from .tetrahedron_mesh import TetrahedronMesh
from .triple_product import TripleProduct
from .unconverged import Unconverged
from .walltime import Walltime
from .zbrent import Zbrent
from .zheev import Zheev
from .zpotrf import Zpotrf

# These handlers depend on other handlers above. So we make sure they are
# imported last and disable isort for them.
# isort: split
from .tetirr import Tetirr
