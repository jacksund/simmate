# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import os
import json
import numpy
from datetime import timedelta

from pymatgen.io.vasp.outputs import Vasprun

from prefect import Flow, Parameter, task
from prefect.triggers import all_finished
from prefect.storage import Local as LocalStorage

from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import VaspCalcC, Pathway as Pathway_DB
from simmate.workflows.diffusion.utilities import (
    run_vasp_custodian_neb,
    get_oxi_supercell_path,
    empty_directory,
)

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
    calc = VaspCalcC(status="S", pathway_id=pathway_id)
    calc.save()


# --------------------------------------------------------------------------------------


@task
def get_images(path):

    # convert the path to a supercell
    path_supercell = get_oxi_supercell_path(path, min_sl_v=7)

    # grab the start, midpoint, and endpoint structures (idpp relaxed)
    # For testing, you can use path.write_path() to visualize these structures
    images = path_supercell.get_structures(nimages=1, idpp=True)

    # BUG: if the idpp relaxation fails, it doesn't raise an error but instead
    # outputs an image filled with sites that have coord (nan, nan, nan). These
    # make empty poscars that just hang in VASP. I check the midpoint image for this
    # and see if any coord is listed as "nan"
    if numpy.isnan(images[1].frac_coords.sum()):
        raise Exception("nan located in midpoint image -- IDPP failed")

    return images


@task  # (timeout=30*60)
def run_vasp(structures, vasp_cmd="mpirun -n 16 vasp_std"):

    # These are the settings I've changed relative to MPStaticSet, where the ones
    # still commented out are ones I'd consider changing if I'm doing a lower-quality
    # calculation.
    custom_incar = dict(
        #
        # For static calc
        # NSW=0,
        # IBRION=-1,
        # For Relax
        NSW=10,  # don't do more than 10 ionic steps
        ISIF=3,
        EDIFFG=-0.1,
        IBRION=2,  # 2 for bad initial guess
        #
        # Turn off / reduce settings for low-quality
        EDIFF=1.0e-05,  # was EDIFF_PER_ATOM=5.0e-05
        # ENCUT=400,  # was 520 --> reduced for fast rough calcs
        # ICHARG=1,  # Read into this. There may be speedup from this setting
        # ISPIN=1,  # was 2 --> spin-polarized turned off for rough calcs
        # LASPH=False,  # was True --> turned off for rough calcs
        # ALGO="Fast",  # Fast for geom_opt, Normal for static
        LDAU=False,  # Turns off +U setting for low-quality calcs (following MITNEBSet)
        #
        # Turn off verbosity & extra file-writing
        LDAUPRINT=0,  # was 1 --> Turned off verbosity of +U routines
        LORBIT=None,  # was 11 --> Turned off writing of PROCAR and DOSCAR
        LAECHG=False,  # don't write out the  AECCARs
        # LCHARG=False,  # don't write out the CHG or CHGCAR
        LVTOT=False,  # don't write the LOCPOT
        #
        # Extra settings
        # KSPACING=0.5,
        NPAR=1,  # for parallel efficiency
        # IVDW=11,  # use DFT-D3 corrections
        ISYM=0,  # Turn off symmetry for vacancy-based diffusion calcs
    )

    # make sure we have a clean directory before starting
    # empty_directory()

    # Run VASP using the structure, custom settings, and custodian
    run_vasp_custodian_neb(
        structures,
        errorhandler_settings="md",  # minimal checks
        vasp_cmd=vasp_cmd,
        # gamma_vasp_cmd="mpirun -n 20 vasp_gamma",
        custom_incar_neb=custom_incar,
        custom_incar_endpoints=custom_incar,  # I just use the same. let set handle NSW and NEB settings
        # reciprocal_density=50,  # very low density kpt mesh
    )

    # grab the custodian log
    # json_log = json.load("custodian.json")

    # These are collective lists that will each have 3 entries
    # (one for each image: start, midpoint, end)
    structures_relaxed = []
    energies_steps = []
    forces = []
    stresses = []
    energies = []
    converged = []
    for directory in ["00", "", "02"]:  # midpoint isn't in 01, but in parent dir (".")

        try:
            # workup the vasp calculation
            # load the xml file and only parse the bare minimum
            xmlReader = Vasprun(
                filename=os.path.join(directory, "vasprun.xml"),
                parse_dos=False,
                parse_eigen=False,
                parse_projected_eigen=False,
                parse_potcar_file=False,
                exception_on_bad_xml=True,
            )

            # check if the calculation converged
            assert xmlReader.converged_electronic  # This MUST be true
            # This likely won't be true bc we limited the calculation to only 10 ionic steps (NSW=10)
            # Because this is expected, we record it just it case it actually did converge
            is_converged = xmlReader.converged_ionic

            # grab the forces, stress, and energies for each ionic step and record
            # these in a collected list.
            f = []
            s = []
            e = []
            for ionic_step in xmlReader.ionic_steps:
                f.append(ionic_step["forces"])
                s.append(ionic_step["stress"])
                e.append(ionic_step["e_wo_entrp"])

            # grab the final structure and energy
            final_structure = xmlReader.structures[-1]
            energy = xmlReader.final_energy

            # add to results list
            energies_steps.append(e)
            forces.append(f)
            stresses.append(s)
            structures_relaxed.append(final_structure)
            energies.append(energy)
            converged.append(is_converged)

        except:
            energies_steps.append([])
            forces.append([[]])
            stresses.append([])
            structures_relaxed.append(None)
            energies.append(None)
            converged.append(False)

    # empty the directory once we are done (note we will not reach this point
    # if the calculation fails above)
    # empty_directory()

    # return the desired info
    return {
        "structures": structures_relaxed,
        "energies": energies,
        "energies_steps": energies_steps,
        "forces": forces,
        "stresses": stresses,
        "converged": converged,
    }


# --------------------------------------------------------------------------------------


@task(max_retries=3, retry_delay=timedelta(seconds=5))  # trigger=all_finished,
def add_results_to_db(output_data, pathway_id):

    # unpack data
    s_start, s_midpoint, s_end = output_data["structures"]
    e_start, e_midpoint, e_end = output_data["energies"]
    es_start, es_midpoint, es_end = output_data["energies_steps"]
    f_start, f_midpoint, f_end = output_data["forces"]
    st_start, st_midpoint, st_end = output_data["stresses"]
    c_start, c_midpoint, c_end = output_data["converged"]
    s_start, s_midpoint, s_end = output_data["structures"]

    # grab the pathway_id entry. This should exists already in the Submitted state
    # An error will be thrown if it's not in the submitted state -- meaning we
    # are trying to overwrite results, which we shouldn't do.
    calc = VaspCalcC.objects.get(pathway_id=pathway_id, status="S")

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

    calc.structure_start_json = s_start.to_json() if s_start else None
    calc.structure_midpoint_json = s_midpoint.to_json() if s_midpoint else None
    calc.structure_end_json = s_end.to_json() if s_end else None

    calc.converged_start = c_start
    calc.converged_midpoint = c_midpoint
    calc.converged_end = c_end
    
    calc.forces_start_json = json.dumps(f_start)
    calc.forces_midpoint_json = json.dumps(f_midpoint)
    calc.forces_end_json = json.dumps(f_end)
    
    calc.stress_start_json = json.dumps(st_start)
    calc.stress_midpoint_json = json.dumps(st_midpoint)
    calc.stress_end_json = json.dumps(st_end)
    
    calc.energysteps_start_json = json.dumps(es_start)
    calc.energysteps_midpoint_json = json.dumps(es_midpoint)
    calc.energysteps_end_json = json.dumps(es_end)

    calc.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("Vasp Calc C") as workflow:

    vasp_cmd = Parameter("vasp_cmd", default="mpirun -n 28 vasp_std")

    # load the structure object from our database
    pathway_id = Parameter("pathway_id")

    # register that the flow is being ran in our result database
    register_run(pathway_id)

    # load the pathway
    path = load_pathway_from_db(pathway_id)

    # convert the path to the supercell images
    images = get_images(path)

    # for each image, run vasp and get the result energy
    output_data = run_vasp(images, vasp_cmd)

    # save the data to our database
    add_results_to_db(output_data, pathway_id)

# for Prefect Cloud compatibility, set the storage to an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

# NOTE TO USER -- because Custodian doesn't really have working-directory control
# I need to run everything in the same directory. Therefore, do NOT run this workflow's
# tasks in parallel

# --------------------------------------------------------------------------------------
