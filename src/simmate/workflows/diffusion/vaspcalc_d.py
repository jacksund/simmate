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
from simmate.database.diffusion import VaspCalcD, Pathway as Pathway_DB
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
    calc = VaspCalcD(status="S", pathway_id=pathway_id)
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
        NSW=3,  # don't do more than N ionic steps
        ISIF=3,
        EDIFFG=5e-4,
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
    converged = []
    times = []
    error_times = []
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

            # grab the final structure
            final_structure = xmlReader.structures[-1]
            
            # we want to know the time spent on failed calculations. I find this
            # by comparing the POTCAR file timestamp to that of the very last
            # error.*.tar.gz file.
            dir_poscar = directory if directory != "" else "01" # !!! BUG w. where POSCAR is for midpoint
            start_time = os.path.getmtime(os.path.join(dir_poscar, "POSCAR"))
            all_errors = [filename for filename in os.listdir(dir_poscar) if "error." in filename]
            all_errors.sort()
            if all_errors:
                final_error_time = os.path.getmtime(os.path.join(dir_poscar, all_errors[-1]))
                total_error_time = final_error_time - start_time
            else:
                total_error_time = 0
            
            # For the vasp calculation that was successful, we also want the 
            # time spent on each ionic step. This info is in the OUTCAR
            with open(os.path.join(dir_poscar, "OUTCAR")) as file:
                filelines = file.readlines()
            time_lines = [line for line in filelines if "time" in line.lower()]
            # the "Total CPU Time used" is the 3rd to last line (if the calc completed successfully)
            # There is also the "Total Elapsed Time" which includes all overhead. We select this one.
            # total_time_line = time_lines[-1]
            # total_time = float(total_time_line.split()[-1])
            # the time of each ionic step has "LOOP+" in it
            ionic_step_time_lines = [line for line in time_lines if "LOOP+" in line]
            # there is a real time and a cpu time (real is slightly extra). We take the cpu time
            ionic_step_times = [float(line.split()[-4][:-1]) for line in ionic_step_time_lines]

            # add to results list
            energies_steps.append(e)
            forces.append(f)
            stresses.append(s)
            structures_relaxed.append(final_structure)
            converged.append(is_converged)
            times.append(ionic_step_times)
            error_times.append(total_error_time)

        except:
            energies_steps.append([])
            forces.append([[]])
            stresses.append([])
            structures_relaxed.append(None)
            converged.append(False)
            times.append([])
            error_times.append(None)

    # empty the directory once we are done (note we will not reach this point
    # if the calculation fails above)
    # empty_directory()

    # return the desired info
    return {
        "structures": structures_relaxed,
        "energies_steps": energies_steps,
        "forces": forces,
        "stresses": stresses,
        "converged": converged,
        "times": times,
        "error_times": error_times,
    }


# --------------------------------------------------------------------------------------


@task(max_retries=3, retry_delay=timedelta(seconds=5))  # trigger=all_finished,
def add_results_to_db(output_data, pathway_id):

    # unpack data
    s_start, s_midpoint, s_end = output_data["structures"]
    es_start, es_midpoint, es_end = output_data["energies_steps"]
    f_start, f_midpoint, f_end = output_data["forces"]
    st_start, st_midpoint, st_end = output_data["stresses"]
    c_start, c_midpoint, c_end = output_data["converged"]
    s_start, s_midpoint, s_end = output_data["structures"]
    t_start, t_midpoint, t_end = output_data["times"]
    et_start, et_midpoint, et_end = output_data["error_times"]

    # grab the pathway_id entry. This should exists already in the Submitted state
    # An error will be thrown if it's not in the submitted state -- meaning we
    # are trying to overwrite results, which we shouldn't do.
    calc = VaspCalcD.objects.get(pathway_id=pathway_id, status="S")

    # now add the empirical data using the supplied dictionary
    # NOTE: the "if not __ else None" code is to make sure there wasn't an error
    # raise in one of the upstream tasks. For example there was an error, oxi_data
    # would be an excpetion class -- in that case, we choose to store None instead
    # of the exception itself.
    calc.status = "C"

    calc.structure_start_json = s_start.to_json() if s_start else None
    calc.structure_midpoint_json = s_midpoint.to_json() if s_midpoint else None
    calc.structure_end_json = s_end.to_json() if s_end else None

    calc.converged_start = c_start
    calc.converged_midpoint = c_midpoint
    calc.converged_end = c_end
    
    calc.error_time_start = et_start
    calc.error_time_midpoint = et_midpoint
    calc.error_time_end = et_end
    
    calc.forces_start_json = json.dumps(f_start)
    calc.forces_midpoint_json = json.dumps(f_midpoint)
    calc.forces_end_json = json.dumps(f_end)
    
    calc.stress_start_json = json.dumps(st_start)
    calc.stress_midpoint_json = json.dumps(st_midpoint)
    calc.stress_end_json = json.dumps(st_end)
    
    calc.energysteps_start_json = json.dumps(es_start)
    calc.energysteps_midpoint_json = json.dumps(es_midpoint)
    calc.energysteps_end_json = json.dumps(es_end)

    calc.timesteps_start_json = json.dumps(t_start)
    calc.timesteps_midpoint_json = json.dumps(t_midpoint)
    calc.timesteps_end_json = json.dumps(t_end)

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
