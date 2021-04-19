# -*- coding: utf-8 -*-

import os
import shlex
import copy

from pymatgen.io.vasp.sets import MITRelaxSet, MITNEBSet  # MPStaticSet
from pymatgen.core.sites import PeriodicSite
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator

from pymatgen_diffusion.neb.pathfinder import MigrationPath  # DistinctPathFinder

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
from custodian.vasp.jobs import VaspJob, VaspNEBJob
from custodian.vasp.validators import VasprunXMLValidator, VaspFilesValidator

# --------------------------------------------------------------------------------------


def get_oxi_supercell_path(path, min_sl_v=None, oxi=False):

    if oxi:
        # add oxidation states to structure
        structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure
    else:
        structure = path.symm_structure

    # Update the specie string
    if oxi:
        # We need to grab the site species and make sure it is the proper oxidation
        # state if we had oxi=True above. Be careful with this because
        # pymatgen-diffusion iindex/eindex really refers to the symm_struct
        # index, not the structure[index]. Therefore, we look at the symm_struct's
        # equivalent sites, grab the first site (bc they are all the same) and
        # see what specie it is.
        specie = structure.equivalent_sites[path.iindex][0].specie
    else:
        # if no oxidation analysis was done, its the same as before
        specie = path.isite.specie

    # convert the structure to a supercell if min_sl_v was provided
    structure_supercell = structure.copy()
    if min_sl_v:
        structure_supercell = structure.copy()
        supercell_size = [
            (min_sl_v // length) + 1 for length in structure_supercell.lattice.lengths
        ]
        structure_supercell.make_supercell(supercell_size)

    isite_new = PeriodicSite(
        species=specie,
        coords=path.isite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )
    esite_new = PeriodicSite(
        species=specie,
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


# --------------------------------------------------------------------------------------


def run_vasp_custodian(
    structure,  # for "neb" this is STRUCTURES! (so a list of structures)
    job_type="normal",  # other option is "neb"
    half_kpts_for_neb=False,  # consider changing this for rough NEB calcs
    errorhandler_settings="default",
    vasp_cmd="mpirun -n 16 vasp",
    # gamma_vasp_cmd="mpirun -n 16 vasp_gamma",
    custom_incar={},
    # reciprocal_density=64,  # MIT uses "length", which I won't mess with
):
    """
    All of this code is a simplified version of...
        atomate.vasp.fireworks.StaticFW
    Note, this firework breaks down into in firetasks, where the main one is...
        atomate.vasp.firetasks.RunVaspCustodian
    """

    # Because shell=True is a secuirity problem, we need to convert the command
    # via shlex so that Popen can read it.
    # Also " > vasp.out" is automatically added by custodian
    vasp_cmd = os.path.expandvars(vasp_cmd)  # if you have "$MY_ENV_VAR" in your command
    vasp_cmd = shlex.split(vasp_cmd)  # convert "mycmd --args" to ["mycmd", "--args"]

    # construct jobs, which is just a single VASP calculation for now. Depending on the
    # job type (normal or neb), I need to all decide which pymatgen input set to use.
    # BUG: vasp_gamma appears to have a bug so I turn it off in all cases
    if job_type == "normal":
        # whether this is a static or relax calc, we use MITRelaxSet as the base
        vasp_input_set = MITRelaxSet(
            structure,
            user_incar_settings=custom_incar,
            # considered PBE_54, but +U or MagMom may change for that
            # user_potcar_functional="PBE",
        )
        jobs = [VaspJob(vasp_cmd, backup=False, auto_gamma=False)]
    elif job_type == "neb":
        # For NEB calcs, we use the MITRelaxSet as the base.
        vasp_input_set = MITNEBSet(
            structure,
            user_incar_settings=custom_incar,
            # considered PBE_54, but +U or MagMom may change for that
            user_potcar_functional="PBE",
        )
        jobs = [
            VaspNEBJob(
                vasp_cmd,
                half_kpts=half_kpts_for_neb,
                backup=False,
                auto_gamma=False,
                auto_npar=False,
            )
        ]

    # The first firetask is to just write the static input. I assume MPStaticSet here.
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

    # For now, I always use these validators. These may be removed for NEB though.
    if job_type == "normal":
        validators = [VasprunXMLValidator(), VaspFilesValidator()]
    elif job_type == "neb":
        validators = []

    # now put all of the jobs and error handlers together
    custodian = Custodian(
        errorhandlers,
        jobs,
        validators=validators,
        max_errors=5,
        polling_time_step=10,  # default 10
        monitor_freq=30,  # default 30
    )

    # BUG: Cloudpickle fails to handle Custodian outputs properly. So I decided
    # to catch the errors here and return a simple error that cloudpickle can handle.
    # In the future, I need to drop Custodian dependency.
    try:
        custodian.run()
    except Exception as exception:
        # I raise only the Custodian error message. The issue is with
        # exception.validator on the ValidationError.
        raise Exception(str(exception))


# --------------------------------------------------------------------------------------


def run_vasp_custodian_neb(
    structures,  # list of all images, including the endpoints
    half_kpts_for_neb=False,  # consider changing this for rough NEB calcs
    errorhandler_settings="no_handler",
    vasp_cmd="mpirun -n 30 vasp_std",
    # gamma_vasp_cmd="mpirun -n 16 vasp_gamma",
    custom_incar_endpoints={},
    custom_incar_neb={},
    # reciprocal_density=64,  # MIT uses "length", which I won't mess with
):
    """
    this is a terrible function becuase Custodian doesn't have dir management...
    I'm only using this in the short term so I can wrap up my project with custodian.
    """

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
    
    # Giving each calc their own unique copies
    errorhandlers1 = errorhandler_groups[errorhandler_settings]
    errorhandlers2 = copy.deepcopy(errorhandlers1)
    errorhandlers3 = copy.deepcopy(errorhandlers1)

    # make sure command is in correct format
    vasp_cmd = os.path.expandvars(vasp_cmd)
    vasp_cmd = shlex.split(vasp_cmd)
    
    # We need two jobs -- one for each endpoint. And then a third job for NEB.
    vasp_input_set = MITRelaxSet(
        structures[0],
        user_incar_settings=custom_incar_endpoints,
        # considered PBE_54, but +U or MagMom may change for that
        user_potcar_functional="PBE",
    )
    jobs = [VaspJob(vasp_cmd, backup=False, auto_gamma=False)]
    run_custodian_robust(vasp_input_set, errorhandlers1, jobs, [], dir="00")
    #
    vasp_input_set = MITRelaxSet(
        structures[-1],
        user_incar_settings=custom_incar_endpoints,
        # considered PBE_54, but +U or MagMom may change for that
        user_potcar_functional="PBE",
    )
    jobs = [VaspJob(vasp_cmd, backup=False, auto_gamma=False)]
    run_custodian_robust(
        vasp_input_set, errorhandlers2, jobs, [], dir=str(len(structures)-1).zfill(2)
    )
    ##

    # For NEB calcs, we use the MITRelaxSet as the base.
    vasp_input_set = MITNEBSet(
        structures,
        user_incar_settings=custom_incar_neb,
        # considered PBE_54, but +U or MagMom may change for that
        user_potcar_functional="PBE",
    )
    jobs = [
        VaspNEBJob(
            vasp_cmd,
            output_file="vasp.out",  # to fix bug with error handlers
            half_kpts=half_kpts_for_neb,
            backup=False,
            auto_gamma=False,
            auto_npar=False,
        )
    ]
    run_custodian_robust(vasp_input_set, errorhandlers3, jobs, [])


def run_custodian_robust(vasp_input_set, errorhandlers, jobs, validators, dir=None):
    """
    This function only exists for NEB right now -- where I'm jumping directories
    """

    # now put all of the jobs and error handlers together
    custodian = Custodian(
        errorhandlers,
        jobs,
        validators=[],
        max_errors=5,
        polling_time_step=10,  # default 10
        monitor_freq=30,  # default 30
    )

    try:
        if dir:
            os.mkdir(dir)
            os.chdir(dir)
        vasp_input_set.write_input(".")
        custodian.run()
    except Exception as exception:
        raise Exception(str(exception))
    finally:
        if dir:
            os.chdir("..")


# --------------------------------------------------------------------------------------


def empty_directory():

    # BUG: because Custodian doesn't let you set the working directory, we
    # need to clear our current directory of any past calculations
    # Delete all files except submit.sh and prefect_agent.py.
    # An error will be thrown if there is a directory present (such as from an
    # NEB calc).
    for filename in os.listdir("."):
        if filename not in ["submit.sh", "slurm.out", "python.out"]:
            os.remove(filename)
