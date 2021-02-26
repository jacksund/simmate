# -*- coding: utf-8 -*-

import os
import shlex

from pymatgen.io.vasp.sets import MPStaticSet
from pymatgen.core.sites import PeriodicSite
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder, MigrationPath

from custodian import Custodian
from custodian.vasp.handlers import (
    VaspErrorHandler,
    AliasingErrorHandler,
    MeshSymmetryErrorHandler,
    UnconvergedErrorHandler,
    # MaxForceErrorHandler,
    PotimErrorHandler,
    FrozenJobErrorHandler,
    NonConvergingErrorHandler,
    PositiveEnergyErrorHandler,
    # WalltimeHandler,
    StdErrHandler,
    DriftErrorHandler,
    LargeSigmaHandler,
    IncorrectSmearingHandler,
    ScanMetalHandler,
)
from custodian.vasp.jobs import VaspJob
from custodian.vasp.validators import VasprunXMLValidator, VaspFilesValidator

# --------------------------------------------------------------------------------------


def get_oxi_supercell_path(path, min_sl_v=None, oxi=False):

    if oxi:
        # add oxidation states to structure
        structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure
    else:
        structure = path.symm_structure

    structure_supercell = structure.copy()
    if min_sl_v:
        structure_supercell = structure.copy()
        supercell_size = [
            (min_sl_v // length) + 1 for length in structure_supercell.lattice.lengths
        ]
        structure_supercell.make_supercell(supercell_size)

    isite_new = PeriodicSite(
        species=structure[path.iindex].specie,  # make sure to grab new oxi state
        coords=path.isite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )
    esite_new = PeriodicSite(
        species=structure[path.eindex].specie,  # make sure to grab new oxi state
        coords=path.esite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )

    path_new = MigrationPath(isite_new, esite_new, structure_supercell)
    # BUG: the init script for MigrationPath can't identify the site indexes properly
    # but they should be the same as before because it is a symmetrized structure. Note
    # that even if I'm wrong in some case -- this will have no effect because iindex
    # and eindex are only used in one portion of the hash as well as for printing
    # the __str__ of the object.
    path_new.iindex = path.iindex
    path_new.eindex = path.eindex

    return path_new


def get_oxi_supercell_path_OLD(structure, path, min_sl_v):

    # if desired, add oxidation states to structure
    structure = ValenceIonicRadiusEvaluator(structure).structure

    # make the supercell
    supercell = structure.copy()
    supercell_size = [(min_sl_v // length) + 1 for length in supercell.lattice.lengths]
    supercell.make_supercell(supercell_size)

    # run the pathway analysis using the supercell structure
    dpf = DistinctPathFinder(
        structure=supercell,
        migrating_specie="F-",
        max_path_length=path.length + 1e-5,  # add extra for rounding errors
        symprec=0.1,
        perc_mode=None,
    )

    # go through paths until we find a match
    # assume we didn't find a match until proven otherwise
    found_match = False
    for path_check in dpf.get_paths():
        if (
            abs(path.length - path_check.length) <= 1e-5  # capture rounding error
            and path.iindex == path_check.iindex
            and path.eindex == path_check.eindex
        ):
            # we found a match so break. No need to check any other pathways.
            found_match = True
            break

    # Just in case we didn't find a match, we need to raise an error
    if not found_match:
        raise Exception("Failed to find the equivalent pathway in the supercell")

    # we now have path_check as the equivalent pathway. This is what the user
    # wants so we can return it
    return path_check


# --------------------------------------------------------------------------------------

def run_vasp_custodian(
    structure,
    errorhandler_settings="default",
    vasp_cmd="mpirun -n 20 vasp",
    gamma_vasp_cmd="mpirun -n 20 vasp_gamma",
    custom_incar={},
    reciprocal_density=64,
):

    # All of this code is a simplified version of...
    #   atomate.vasp.fireworks.StaticFW
    # Note, this firework breaks down into in firetasks

    # Because shell=True is a secuirity problem, we need to convert the command
    # via shlex so that Popen can read it.
    # Also " > vasp.out" is automatically added by custodian
    vasp_cmd = os.path.expandvars(vasp_cmd)  # if you have "$MY_ENV_VAR" in your command
    vasp_cmd = shlex.split(vasp_cmd)  # convert "mycmd --args" to ["mycmd", "--args"]

    # The first firetask is to just write the static input. I assume MPStaticSet here.
    vasp_input_set = MPStaticSet(
        structure,
        user_incar_settings=custom_incar,
        # defaults are 64 for Relax, 100 for Static
        reciprocal_density=reciprocal_density,
        # considered PBE_54, but +U or MagMom may change for that
        user_potcar_functional="PBE",
    )
    vasp_input_set.write_input(".")

    # The next firetask is to run VASP using Custodian. This code is a simplified
    # version of atomate.vasp.firetasks.RunVaspCustodian

    # These are the error handlers used by the Materials Project (via Atomate)
    errorhandler_groups = {
        "default": [
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
        ],
        "strict": [
            VaspErrorHandler(),
            MeshSymmetryErrorHandler(),
            UnconvergedErrorHandler(),
            NonConvergingErrorHandler(),
            PotimErrorHandler(),
            PositiveEnergyErrorHandler(),
            FrozenJobErrorHandler(),
            StdErrHandler(),
            AliasingErrorHandler(),
            DriftErrorHandler(),
            LargeSigmaHandler(),
            IncorrectSmearingHandler(),
        ],
        "scan": [
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
            ScanMetalHandler(),
        ],
        "md": [VaspErrorHandler(), NonConvergingErrorHandler()],
        "no_handler": [],
    }

    # based on input flag, select which handlers we will be using
    errorhandlers = errorhandler_groups[errorhandler_settings]

    # For now, I always use these validators. These may be remove for NEB though.
    validators = [VasprunXMLValidator(), VaspFilesValidator()]

    # construct jobs
    jobs = [VaspJob(vasp_cmd, backup=False)]

    custodian = Custodian(
        errorhandlers,
        jobs,
        validators=validators,
        max_errors=5,
        polling_time_step=5,  # default 10
        monitor_freq=3,  # default 30
    )

    custodian.run()


def empty_directory():

    # BUG: because Custodian doesn't let you set the working directory, we
    # need to clear our current directory of any past calculations
    # Delete all files except submit.sh and prefect_agent.py.
    # An error will be thrown if there is a directory present (such as from an
    # NEB calc).
    for filename in os.listdir("."):
        if not "submit.sh" and not "prefect_agent.py":
            os.remove(filename)
