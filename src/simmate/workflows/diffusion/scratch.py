# -*- coding: utf-8 -*-

from datetime import timedelta

from pymatgen.io.vasp.outputs import Vasprun

from prefect import Flow, Parameter, task
from prefect.triggers import all_finished
from prefect.storage import Local as LocalStorage

from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import VaspCalcA, Pathway as Pathway_DB
from simmate.workflows.diffusion.utilities import (
    run_vasp_custodian,
    get_oxi_supercell_path,
    empty_directory,
)

"""
# A standard CI-NEB calculation
# Comment the item to use the default settings.
# Note that "fireworks" is a list corresponding to the order of execution.
# Author: Hanmei Tang (UCSD)
fireworks:
# Relaxation for parent structure
- fw: atomate.vasp.fireworks.core.NEBRelaxationFW
  user_incar_settings:
    EDIFF: 1e-5
    EDIFFG: -0.02
    LDAU: False
    NPAR: 4
    NSW: 200
  user_kpoints_settings:
    grid_density: 100
  additional_cust_args:
    auto_npar: False
    gzip_output: False

# Two endpoints relaxations
- fw: atomate.vasp.fireworks.core.NEBRelaxationFW
  user_incar_settings:
    EDIFF: 1e-5
    EDIFFG: -0.02
    NPAR: 4
    NSW: 500
  user_kpoints_settings:
    grid_density: 100
  additional_cust_args:
    auto_npar: False
    gzip_output: False

# First round NEB (coarse)
- fw: atomate.vasp.fireworks.core.NEBFW
  user_incar_settings:
    EDIFFG: -0.05
    IOPT: 7
    NPAR: 4
  user_kpoints_settings:
    grid_density: 100
  additional_cust_args:
    auto_npar: False
    gzip_output: False

# Second round NEB (fine)
- fw: atomate.vasp.fireworks.core.NEBFW
  user_incar_settings:
    EDIFFG: -0.03
    EDIFFG: -0.03
    IOPT: 1
  user_kpoints_settings:
    grid_density: 100
  additional_cust_args:
    auto_npar: False
    gzip_output: False

# These will update spec_default in neb.py
common_params:
  _category: ""
  wf_name: lio2_neb_workflow
  is_optimized: False  # for calcluation from ep and parent
  # additional_ep_params:
  idpp_species: ["Li"]  # List of string
  site_indices: [0, 1]
  interpolation_type: "IDPP"
  # Distance tolerance (in Angstrom) used to match the atomic indices between
  # start and end structures. If it is set 0, then no sorting will be performed.
  sort_tol: 0
  # Distance in Angstrom, used in calculating number of images.
  d_img: 0.7
  neb_walltime: "10:00:00"  # set NEB walltime to 10 hours
"""



# Relaxing the endpoint structures
# from pymatgen_diffusion.neb.io import MVLCINEBEndPointSet
# vasp_input_set = MVLCINEBEndPointSet(
#     structure,
#     user_incar_settings=user_incar_settings,
#     user_kpoints_settings=user_kpoints_settings,
# )
# cust_args = {
#     "job_type": "normal",
#     "gzip_output": False,
#     "handler_group": "no_handler",
# }
# cust_args.update(additional_cust_args)
# run_vasp = RunVaspCustodian(
#     vasp_cmd=">>vasp_cmd<<", gamma_vasp_cmd=">>gamma_vasp_cmd<<", **cust_args
# )

# getting all NEB images
# nimages = path.length // 0.7  # so 1 image per 0.7 Angstroms
# from pymatgen_diffusion.neb.pathfinder import IDPPSolver
# obj = IDPPSolver.from_endpoints([ep0, ep1], nimages=nimages)
# images = obj.run(species=idpp_species)

# Writing all images for CI-NEBSet
# from pymatgen_diffusion.neb.io import MVLCINEBSet
# vis = MVLCINEBSet(images, user_incar_settings=user_incar_settings,
#                   user_kpoints_settings=user_kpoints_settings)
# vis.write_input(".")

# Running NEB via Custodian
# cust_args = {
#     "job_type": "neb",
#     "gzip_output": False,
#     "handler_group": "no_handler",
# }
# cust_args.update(additional_cust_args)
# run_neb_task = RunVaspCustodian(
#     vasp_cmd=">>vasp_cmd<<", gamma_vasp_cmd=">>gamma_vasp_cmd<<", **cust_args
# )


# --------------------------------------------------------------------------------------


@task
def load_pathway_from_db(pathway_id):

    # grab the pathway model object
    pathway_db = Pathway_DB.objects.get(id=pathway_id)

    # convert the pathway to pymatgen MigrationPath
    path = pathway_db.to_pymatgen()

    return path


@task
def register_run(pathway_id):

    # create the file and indicate that it has been submitted
    calc = VaspCalcA(status="S", pathway_id=pathway_id)
    calc.save()


# --------------------------------------------------------------------------------------


@task
def get_images(path):

    # convert the path to a supercell
    path_supercell = get_oxi_supercell_path(path, min_sl_v=7)

    # grab the start, midpoint, and endpoint structures (idpp relaxed)
    # For testing, you can use path.write_path() to visualize these structures
    images = path_supercell.get_structures(nimages=1, idpp=True)

    return images


@task  # (timeout=30*60)
def run_vasp(structure):

    # These are the settings I've changed relative to MPStaticSet, where the ones
    # still commented out are ones I'd consider changing if I'm doing a lower-quality
    # calculation.
    custom_incar = dict(
        EDIFF=1.0e-02,  # was EDIFF_PER_ATOM=5.0e-05
        # ENCUT=400,  # was 520 --> reduced for fast rough calcs
        # ICHARG=1,  # Read into this. There may be speedup from this setting
        # ISPIN=1,  # was 2 --> spin-polarized turned off for rough calcs
        # LASPH=False,  # was True --> turned off for rough calcs.
        ALGO="Fast",  # Fast for geom_opt, Normal for static
        LDAU=False,  # Turns off +U setting for low-quality calcs (following MITNEBSet)
        LDAUPRINT=0,  # was 1 --> Turned off verbosity of +U routines
        LORBIT=None,  # was 11 --> Turned off writing of PROCAR and DOSCAR
        LAECHG=False,  # don't write out the  AECCARs
        LCHARG=False,  # don't write out the CHG or CHGCAR
        LVTOT=False,  # don't write the LOCPOT
        # KSPACING=0.5,
        NPAR=1,  # for parallel efficiency
        # IVDW=11,  # use DFT-D3 corrections
        ISYM=0,  # Turn off symmetry for vacancy-based diffusion calcs
    )

    # make sure we have a clean directory before starting
    empty_directory()

    # Run VASP using the structure, custom settings, and custodian
    run_vasp_custodian(
        structure,
        errorhandler_settings="default",  # minimal checks
        # vasp_cmd="mpirun -n 20 vasp",
        # gamma_vasp_cmd="mpirun -n 20 vasp_gamma",
        custom_incar=custom_incar,
        reciprocal_density=64,  # very low density kpt mesh
    )

    # grab the custodian log
    # json_log = json.load("custodian.json")

    # workup the vasp calculation
    # load the xml file and only parse the bare minimum
    xmlReader = Vasprun(
        filename="vasprun.xml",
        parse_dos=False,
        parse_eigen=False,
        parse_projected_eigen=False,
        parse_potcar_file=False,
        exception_on_bad_xml=True,
    )

    # confirm that the calculation converged
    assert xmlReader.converged

    # grab the final structure
    # final_structure = xmlReader.structures[-1]
    # grab the energy per atom
    # final_energy = xmlReader.final_energy / final_structure.num_sites

    # empty the directory once we are done (note we will not reach this point
    # if the calculation fails above)
    empty_directory()

    # return the desired info
    return xmlReader.final_energy


# --------------------------------------------------------------------------------------


@task(trigger=all_finished, max_retries=3, retry_delay=timedelta(seconds=5))
def add_results_to_db(energies_mapped, pathway_id):

    # energies_mapped will be a list of three floats
    # e_start, e_midpoint, e_end = energies_mapped
    e_start = energies_mapped[0]
    e_midpoint = energies_mapped[1]
    e_end = energies_mapped[2]

    # grab the pathway_id entry. This should exists already in the Submitted state
    # An error will be thrown if it's not in the submitted state -- meaning we
    # are trying to overwrite results, which we shouldn't do.
    calc = VaspCalcA.objects.get(pathway_id=pathway_id, status="S")

    # now add the empirical data using the supplied dictionary
    # NOTE: the "if not __ else None" code is to make sure there wasn't an error
    # raise in one of the upstream tasks. For example there was an error, oxi_data
    # would be an excpetion class -- in that case, we choose to store None instead
    # of the exception itself.
    calc.status = "C"
    calc.energy_start = e_start if not isinstance(e_start, Exception) else None
    calc.energy_midpoint = e_midpoint if not isinstance(e_midpoint, Exception) else None
    calc.energy_end = e_end if not isinstance(e_end, Exception) else None
    try:
        barrier = max([e_midpoint - e_start, e_midpoint - e_end])
    except:  # TypeError
        barrier = None
    calc.energy_barrier = barrier
    calc.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("Vasp Calc A") as workflow:

    # load the structure object from our database
    pathway_id = Parameter("pathway_id")

    # register that the flow is being ran in our result database
    register_run(pathway_id)

    # load the pathway
    path = load_pathway_from_db(pathway_id)

    # convert the path to the supercell images
    images = get_images(path)

    # for each image, run vasp and get the result energy
    energies = run_vasp.map(images)

    # save the data to our database
    add_results_to_db(energies, pathway_id)

# for Prefect Cloud compatibility, set the storage to an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

# NOTE TO USER -- because Custodian doesn't really have working-directory control
# I need to run everything in the same directory. Therefore, do NOT run this workflow's
# tasks in parallel

# --------------------------------------------------------------------------------------
