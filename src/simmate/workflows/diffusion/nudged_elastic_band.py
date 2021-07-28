# -*- coding: utf-8 -*-

from prefect import task, Flow, Parameter

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder, IDPPSolver
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

# The first task is just to optimize the bulk structure with VASP
relax_bulk_structure = VaspTask(
    incar=dict(
        EDIFF=1.0e-07,
        EDIFFG=-1e-04,
        ENCUT=520,
        ISMEAR=0,
        LCHARG=True,
        LAECHG=True,
        LWAVE=False,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
        KSPACING=0.5,
    ),
    functional="PBE",
)


@task
def make_cubic_supercell(structure, min_sl_vector=8):

    # This task only exists because I'm stuck on pymatgen-diffusion v2020.10.8
    # In this version, I need to pass a supercell into DistinctPathFinder. In
    # future versions, I instead convert to a supercell AFTER I have the paths
    # from DistinctPathFinder.

    # convert the structure to the LLL reduced form
    structure_new = structure.copy(sanitize=True)

    # convert to a supercell
    supercell_size = [
        (min_sl_vector // length) + 1 for length in structure_new.lattice.lengths
    ]
    structure_new.make_supercell(supercell_size)

    return structure_new


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


# The first task is just to optimize the bulk structure with VASP
relax_endpoint_structure = VaspTask(
    incar=dict(
        EDIFF=1.0e-07,
        EDIFFG=-1e-04,
        ENCUT=520,
        ISMEAR=0,
        LCHARG=True,
        LAECHG=True,
        LWAVE=False,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
        KSPACING=0.5,
        ISYM=0,
    ),
    functional="PBE",
)

# Take the two optimized endpoints and make images from them.
# Note that directory here is the base directory where we'll find the 00 and
# nimages+1 folder that the endpoints are in


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
    structure_relaxed = relax_bulk_structure(
        structure=structure,
        directory="bulk_relaxation",
    )

    # convert to cubic supercell
    supercell = make_cubic_supercell(structure=structure_relaxed, min_sl_vector=min_sl_vector)

    # Identify all symmetrically unique pathways
    # TODO: currently I limit results to the first pathway
    pathway = find_all_unique_pathways(supercell, migrating_specie)

    # *** and then the remaindering steps are done for each individual pathway ***

    # Relax the start/end supercell images

    # Interpolate the start/end supercell images and empirically relax these using IDPP.

    # Relax all images using NEB

# --------------------------

# from pymatgen.core.structure import Structure
# from simmate.workflows.diffusion.nudged_elastic_band import workflow
# structure = Structure.from_file("ybof.cif")
# test = workflow.run(structure=structure, migrating_specie="F")
