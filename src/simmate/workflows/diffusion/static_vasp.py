# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 14:38:41 2021

@author: jacks
"""

from pymatgen import Structure
from pymatgen.io.vasp.sets import MPStaticSet

from custodian import Custodian
from custodian.vasp.handlers import (
    VaspErrorHandler,
    # AliasingErrorHandler,
    MeshSymmetryErrorHandler,
    UnconvergedErrorHandler,
    # MaxForceErrorHandler,
    PotimErrorHandler,
    FrozenJobErrorHandler,
    NonConvergingErrorHandler,
    PositiveEnergyErrorHandler,
    # WalltimeHandler,
    StdErrHandler,
    # DriftErrorHandler,
    LargeSigmaHandler,
    IncorrectSmearingHandler,
    # ScanMetalHandler,
)
from custodian.vasp.jobs import VaspJob
from custodian.vasp.validators import VasprunXMLValidator, VaspFilesValidator

vasp_cmd = "vasp_std > vasp.out"
gamma_vasp_cmd = "vasp_gamma > vasp.out"
vasp_input_set_params = {}

# These are the settings I've changed relative to MPStaticSet, where the ones
# still commented out are ones I'd consider changing if I'm doing a lower-quality
# calculation.
custom_incar = dict(
    EDIFF_PER_ATOM=5.0e-05,  # was EDIFF_PER_ATOM=5.0e-05
    # ENCUT=520, # was 520 --> reduced for fast rough calcs
    # ISPIN=2,  # was 2 --> spin-polarized turned off for rough calcs
    # LASPH=True,  # was True --> turned off for rough calcs.
    ALGO="Fast",  # Fast for geom_opt, Normal for static
    LDAUPRINT=0,  # was 1 --> Turned off verbosity of +U routines
    LORBIT=None,  # was 11 --> Turned off writing of PROCAR and DOSCAR
    LAECHG=False,  # don't write out the  AECCARs
    # LCHARG=False,  # don't write out the CHG or CHGCAR -- I keep this for custodian
    LVTOT=False,  # don't write the LOCPOT
    # KSPACING=0.5,
    NPAR=4,  # for parallel efficiency
    # IVDW=11,  # use DFT-D3 corrections
)

structure = Structure.from_file("NaCl.cif")
structure = structure.get_primitive_structure()
structure = structure.copy(sanitize=True)

# to practice working with a supercell + vacancy
structure.make_supercell(4)

# All of this code is a simplified version of...
#   atomate.vasp.fireworks.StaticFW
# Note, this firework breaks down into in firetasks


# The first firetask is to just write the static input. I assume MPStaticSet here.
vasp_input_set = MPStaticSet(
    structure,
    user_incar_settings=custom_incar,
    # defaults are 64 for Relax, 100 for Static
    reciprocal_density=64,
    # considered PBE_54, but +U or MagMom may change for that
    user_potcar_functional="PBE",
)
vasp_input_set.write_input(".")


# The next firetask is to run VASP using Custodian. This code is a simplified
# version of atomate.vasp.firetasks.RunVaspCustodian

# I choose the "default" handler group, but may want the "strict" later on
errorhandlers = [
    VaspErrorHandler(),
    MeshSymmetryErrorHandler(),
    UnconvergedErrorHandler(),
    NonConvergingErrorHandler(),
    PotimErrorHandler(),
    PositiveEnergyErrorHandler(),
    FrozenJobErrorHandler(),
    StdErrHandler(),
    LargeSigmaHandler(),
    IncorrectSmearingHandler(),
    # MaxForceErrorHandler() # This is just for relax, right?
]

validators = [VasprunXMLValidator(), VaspFilesValidator()]

# construct jobs
jobs = [VaspJob(vasp_cmd, backup=False)]

custodian = Custodian(
    errorhandlers,
    jobs,
    validators=validators,
    max_errors=5,
    # polling_time_step=10,
    # monitor_freq=30,
)

custodian.run()

# TODO
# save to database
