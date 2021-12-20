# -*- coding: utf-8 -*-

"""
Nudged elastic band is composed of the following stages...

1. Relax the starting bulk structure

2. Identify all symmetrically unique pathways

*** and then the remaindering steps are done for each individual pathway ***
*** NOTE: this guide only looks at the FIRST diffusion pathway ***

3. Relax the start/end supercell images 
    (or only one of these if they are equivalent)

4. Interpolate the start/end supercell images and empirically relax these
    using IDPP.

5. Relax all images using NEB


For this code to run, you can use the following conda env:
    
    conda create -n neb_env -c conda-forge python=3.8 pymatgen pymatgen-diffusion

And some helpful links for running VASP:
    https://www.vasp.at/wiki/index.php/TS_search_using_the_NEB_Method
    https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/blob/master/pymatgen/analysis/diffusion/neb/io.py

"""

# -----------------------------------------------------------------------------

# STEP 1: The bulk structure

# Start with your fully relaxed bulk structure and load it
from pymatgen.core.structure import Structure

bulk_structure = Structure.from_file("Y2CI2_mp-1206803_primitive.cif")

# I like to convert to the LLL reduced primitive cell to make it as cubic as possible
bulk_structure_lll = bulk_structure.copy(sanitize=True)

# -----------------------------------------------------------------------------

# STEP 2: Identifying diffusion pathways

from pymatgen.analysis.diffusion.neb.pathfinder import DistinctPathFinder


# Use pymatgen to find all the symmetrically unique pathways.
# NOTE: This only finds pathways up until the structure is percolating. If
# you are interested in longer pathways, then this script needs to be adjusted
pathfinder = DistinctPathFinder(
    bulk_structure_lll,
    migrating_specie="I",
)
all_pathways = paths = pathfinder.get_paths()

# grab the shortest path for now (which is the first one)
shortest_pathway = all_pathways[0]

# -----------------------------------------------------------------------------

# STEP 3: Relax the start/end supercell structures

# make the start and end supercell structures of target size
start_supercell, end_supercell, bulk_supercell = shortest_pathway.get_sc_structures(
    vac_mode=False,  # vacancy vs. interstitial diffusion
    min_atoms=80,  # supercell must have at least this many atoms
    max_atoms=240,  # supercell must NOT have this many atoms
    min_length=10,  # supercell must have vectors of at least this length
)
# NOTE: This is a brand new function from pymatgen, but compared to my method in
# the Fluoride paper, it does the same exact thing.
# BUG: vac_mode=True is broken for this. I fixed it for them... but they haven't
# released a new version of this code yet.
# See here:
#   https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/pull/246
#   https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/issues/245

#### RELAX THESE WITH VASP ####
start_supercell.to("poscar", "POSCAR_start")
end_supercell.to("poscar", "POSCAR_end")

# -----------------------------------------------------------------------------

# STEP 4: Use the relaxed start/end supercells to make idpp-relaxed images

from pymatgen.core.structure import Structure

start_supercell = Structure.from_file("CONTCAR_start")
end_supercell = Structure.from_file("CONTCAR_end")

# Interpolate and then IDPP-relax these structures
from pymatgen.analysis.diffusion.neb.pathfinder import IDPPSolver

idpp_solver = IDPPSolver.from_endpoints(
    [start_supercell, end_supercell],
    nimages=7,  # number of images to use
)

images = idpp_solver.run()

# you can write these images to files
# Note: this list of images include the start/end structures as well
for i, image in enumerate(images):
    image.to("poscar", f"POSCAR_{i}") 

# Take the two optimized endpoints and make images from them.
# Note that directory here is the base directory where we'll find the 00 and
# nimages+1 folder that the endpoints are in

# -----------------------------------------------------------------------------

# STEP 5: Relax images using IDPP!

#### RELAX THESE WITH VASP ####
