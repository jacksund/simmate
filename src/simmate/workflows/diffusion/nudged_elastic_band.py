# -*- coding: utf-8 -*-

from prefect import task, Flow, Parameter

from pymatgen.analysis.diffusion.neb.pathfinder import DistinctPathFinder, IDPPSolver
from pymatgen.core.structure import Structure

from simmate.calculators.vasp.tasks.base import VaspTask

"""
Nudged elastic band is composed of the following stages...

1. Relax the starting bulk structure

2. Identify all symmetrically unique pathways

*** and then the remaindering steps are done for each individual pathway ***
*** NOTE: the current build only looks at the FIRST diffusion pathway ***

3. Relax the start/end supercell images 
    (or only one of these if they are equivalent)

4. Interpolate the start/end supercell images and empirically relax these
    using IDPP.

5. Relax all images using NEB

"""

# The a series of tasks is just to optimize the structure with VASP. I can use
# this single class to do it because I turn symmetry off from the start.
# I currently base these off of MITRelaxSet
# https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/vasp/MITRelaxSet.yaml
relax_structure = VaspTask(
    incar=dict(
        ALGO="FAST",
        EDIFF=1.0e-05,
        ENCUT=520,
        IBRION=2,
        ICHARG=1,
        ISIF=3,
        ISMEAR=-5,
        ISPIN=2,
        ISYM=0,
        # LDAU --> These parameters are excluded for now.
        LORBIT=11,
        LREAL="auto",
        LWAVE=False,
        NELM=200,
        NELMIN=6,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
        KSPACING=0.5,  # --> This is VASP default and not the same as pymatgen
    ),
    functional="PBE",
)


@task
def find_all_unique_pathways(structure, migrating_specie):

    # TODO:
    # In the future, I should do the following for this task...
    #   If prexisting pathways exist in the database...
    #       1. return the pathway object
    #   If no pathways exist in the database yet
    #       1. run PathFinder to identify all paths
    #       2. save this pathways to the database
    #       3. return pathway object

    # Use pymatgen to find all the symmetrically unique pathways.
    # NOTE: This only finds pathways up until the structure is percolating. If
    # you are interested in longer pathways, then this script needs to be adjusted
    pathfinder = DistinctPathFinder(
        structure,
        migrating_specie=migrating_specie,
        # max_path_length=5,
        # symprec=0.1,
        # perc_mode=">1d",
    )

    # pull the pathways and return them
    paths = pathfinder.get_paths()
    return paths[0]


# Take the two optimized endpoints and make images from them.
# Note that directory here is the base directory where we'll find the 00 and
# nimages+1 folder that the endpoints are in


@task(nout=2)  # nout means we are returning two items!
def get_endpoints(
    pathway,
    min_length=7,
    min_atoms=40,
    max_atoms=150,
):

    structure_start, structure_end, _ = pathway.get_sc_structures(
        vac_mode=True,  # we assume vacancy-based diffusion for now
        min_length=min_length,
        min_atoms=min_atoms,
        max_atoms=max_atoms,
    )

    return structure_start, structure_end


@task
def get_idpp_images(structure_start, structure_end, nimages=5):

    # set up the solver
    idpp_solver = IDPPSolver.from_endpoints(
        [structure_start, structure_end],
        nimages=nimages,
    )

    # Run the idpp relaxation and grab the relaxed images from the result.
    # Note the output includes the endpoint structures.
    images = idpp_solver.run()

    return images


# now make the overall workflow
with Flow("NEB Analysis") as workflow:

    # These are the input parameters for the overall workflow
    structure = Parameter("structure")
    migrating_specie = Parameter("migrating_specie")
    min_sl_vector = Parameter("min_sl_vector", default=8)
    # nimages = Parameter("nimages", default=5)
    # directory = Parameter("directory", default=".")
    # vasp_cmd = Parameter("vasp_cmd", default="mpirun -n 16 vasp_std")

    # Relax the starting bulk structure
    structure_relaxed = relax_structure(
        structure=structure,
        directory="bulk_relaxation",
    )

    # Identify all symmetrically unique pathways
    # TODO: currently I limit results to the first pathway
    pathway = find_all_unique_pathways(structure_relaxed, migrating_specie)

    # convert to cubic supercell
    start, end = get_endpoints(
        pathway=pathway,
        min_length=min_sl_vector,
    )

    # *** and then the remaindering steps are done for each individual pathway ***

    # Relax the start/end supercell images

    # Interpolate the start/end supercell images and empirically relax these using IDPP.

    # Relax all images using NEB

# --------------------------

# from pymatgen.core.structure import Structure
# from simmate.workflows.diffusion.nudged_elastic_band import workflow
# structure = Structure.from_file("baalgef.cif")
# test = workflow.run(structure=structure, migrating_specie="F")

# --------------------------

# LIST OF SOME ERRORS ENCOUNTERED...

# Fatal error! IBRION=0, but no entry for POTIM on file INCAR. MUST be specified!

# WARNING: type information on POSCAR and POTCAR are incompatible
# POTCAR overwrites the type information in POSCAR

