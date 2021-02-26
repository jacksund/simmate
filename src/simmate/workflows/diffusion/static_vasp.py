# -*- coding: utf-8 -*-

from pymatgen.io.vasp.outputs import Vasprun

from prefect import Flow, Parameter, task
from prefect.storage import Local as LocalStorage

from simmate.workflows.diffusion.utilities import (
    run_vasp_custodian,
    get_oxi_supercell_path,
    empty_directory,
)

# --------------------------------------------------------------------------------------


@task
def load_pathway_from_db(pathway_id):

    from simmate.configuration import django  # ensures setup
    from simmate.database.diffusion import Pathway as Pathway_DB

    # grab the pathway model object
    pathway_db = Pathway_DB.objects.get(id=pathway_id)

    # convert the pathway to pymatgen MigrationPath
    path = pathway_db.to_pymatgen()

    return path


@task
def register_run(pathway_id):

    from simmate.configuration import django  # ensures setup
    from simmate.database.diffusion import VaspCalcA

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


@task
def run_vasp(structure):

    # These are the settings I've changed relative to MPStaticSet, where the ones
    # still commented out are ones I'd consider changing if I'm doing a lower-quality
    # calculation.
    custom_incar = dict(
        EDIFF=1.0e-02,  # was EDIFF_PER_ATOM=5.0e-05
        ENCUT=400,  # was 520 --> reduced for fast rough calcs
        # ICHARG=1,  # READ INTO THIS. There may be speedup from this setting
        ISPIN=1,  # was 2 --> spin-polarized turned off for rough calcs
        LASPH=False,  # was True --> turned off for rough calcs.
        ALGO="Fast",  # Fast for geom_opt, Normal for static
        LDAU=False,  # Turns off +U setting for low-quality calcs (following MITNEBSet)
        LDAUPRINT=0,  # was 1 --> Turned off verbosity of +U routines
        LORBIT=None,  # was 11 --> Turned off writing of PROCAR and DOSCAR
        LAECHG=False,  # don't write out the  AECCARs
        LCHARG=False,  # don't write out the CHG or CHGCAR
        LVTOT=False,  # don't write the LOCPOT
        # KSPACING=0.5,
        NPAR=4,  # for parallel efficiency
        # IVDW=11,  # use DFT-D3 corrections
        ISYM=1,  # Turn off symmetry for vacancy-based diffusion calcs
    )

    # make sure we have a clean directory before starting
    empty_directory()

    # Run VASP using the structure, custom settings, and custodian
    run_vasp_custodian(
        structure,
        errorhandler_settings="md",  # minimal checks
        vasp_cmd="mpirun -n 30 vasp",
        gamma_vasp_cmd="mpirun -n 30 vasp_gamma",
        custom_incar=custom_incar,
        reciprocal_density=50,  # very low density kpt mesh
    )

    # grab the custodian log
    # TODO

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

@task
def add_results_to_db(energies_mapped):

    # energies_mapped will be a list of three floats
    e_start, e_midpoint, e_end = energies_mapped

    from simmate.configuration import django  # ensures setup
    from simmate.database.diffusion import VaspCalcA

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
        barrier = max([e_start - e_midpoint, e_end - e_midpoint])
    except:
        barrier = None
    calc.energy_barrier = barrier
    calc.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("empiricalmeasures-for-pathway") as workflow:

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
    add_results_to_db(energies)

# for Prefect Cloud compatibility, set the storage to a an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

# NOTE TO USER -- because Custodian doesn't really have working-directory control
# I need to run everything in the same directory. Therefore, do NOT run this workflow's
# tasks in parallel

# --------------------------------------------------------------------------------------
