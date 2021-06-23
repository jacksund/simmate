# -*- coding: utf-8 -*-

"""

This file is NOT a script that directly applies the framework used in this
study, but it is intended as a detailed experimental section on how to reproduce our
scientific results. The core framework that is based on django and a custom 
workflow management system is removed for clarity, but it will be detailed and 
open-sourced in a separate study.

Code dependencies...
    - Materials Project database version '2021_02_08'
    - Pymatgen 2020.12.31
    - Pymatgen-diffusion 2020.10.8
    - Matminer 0.6.4
    - Custodian 2021.1.8
    
You can install with...
    conda create -n my_new_enviornment python=3.8;
    conda install -n jacks_env -c conda-forge pymatgen==2020.12.31 pymatgen-diffusion==2020.10.8 custodian==2021.1.8 matminer==0.6.4;

NOTE: you may switch to more-current versions of these dependencies, but API
may vary. You'll have to update the code accordingly. This is especially relevant
with the pymatgen-diffusion package at the time of writing, which is undergoing
significant development.

"""

# --------------------------------------------------------------------------------------

# STAGE 1 -- Source Database

# All fluorine-containing structures are pulled from the Materials Project without
# any other limiting criteria. We used pymatgen's MPRester class to do this.
# Optionally, you can pull extra data such as the energy above hull. Only the 
# "structure" is required for the overall workflow though.
# You can find your personal API key at https://materialsproject.org/open
from pymatgen import MPRester
mpr = MPRester(api_key)
criteria={"elements": {"$all": ["F"]}}
properties=[
        "material_id",
        "final_energy",
        "final_energy_per_atom",
        "formation_energy_per_atom",
        "e_above_hull",
        "structure",
    ]
source_data = mpr.query(criteria, properties)

# --------------------------------------------------------------------------------------

# STAGE 2 -- Structure Santization

# Make sure we have the primitive unitcell first
# We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
# built-in Structure.get_primitive_structure function:
# Default tol is 0.01, but we use a looser 0.1 Angstroms
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
structure = SpacegroupAnalyzer(structure, 0.1).find_primitive()

# Convert the structure to a "sanitized" version.
# This includes...
#   (i) an LLL reduction
#   (ii) transforming all coords to within the unitcell
#   (iii) sorting elements by electronegativity
structure = structure.copy(sanitize=True)

# --------------------------------------------------------------------------------------

# STAGE 3 -- Finding Symmetrically-Unique Pathways

# The pymatgen_diffusion package makes this super easy for us, but note that future
# versions of this package may differ greatly in how you import and use their code.
# To configure our path finder, we limit all pathways to 5 Angstroms. We also use
# a symmetry tolerance of 0.1 to match our settings used above. The "perc_mode"
# is turned off here because we want to determine pathway dimmensionality later
# on, rather than within pathway identification.
from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder
dpf = DistinctPathFinder(
    structure=structure,
    migrating_specie="F",
    max_path_length=5,
    symprec=0.1,
    perc_mode=None,
)

# grab all the paths as MigrationPath objects
# We also limited the number of pathways per structure to the 5 shortest.
paths = dpf.get_paths()[:5]

# --------------------------------------------------------------------------------------

# STAGE 4 -- Oxidation Analysis on Each Pathway

# Oxidation-State Prediction
# Here, we run oxidation analysis on structure and then grab the oxidation state 
# of the diffusing ion
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator
structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure
oxi_state = structure.equivalent_sites[path.iindex][0].specie.oxi_state

# --------------------------------------------------------------------------------------

# STAGE 5 -- Determine Dimensionality for Each Pathway

# We selected the larson method for determining dimensionality
from pymatgen.analysis.dimensionality import get_dimensionality_larsen

# Getting the dimmensionality is a bit trickier because FullPathMapper is written to
# find the structures from scratch. Instead, we already have our pathway and want to
# feed that into the FullPathMapper. The solution is to initialize the class with 
# the same source data and then go through to find matching pathways. Future versions
# of FullPathMapper may simplify this process though.
from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper
fpm = FullPathMapper(
    path.symm_structure,
    path.isite.specie,
    max_path_length=path.length + 1e-5, # plus small number to avoid finite errors
)

# in the current version of this module, we have to manually populate extra fields
fpm.populate_edges_with_migration_paths()
fpm.group_and_label_hops()
fpm.get_unique_hops_dict()

# We need to figure out the correct hop label, and we do this by looking
# at all of them until we have a "graph edge" that matches our target pathway
edges = fpm.s_graph.graph.edges(data=True)
for edge in edges:
    if path == edge[2]["hop"]:
        target_hop_label = edge[2]["hop_label"]
        break

# Delete all but our specific MigrationPath (which has a unique 'hop-label')
# Because we are destroying the structure graph and we still want the original
# copy later, we make a deepcopy of the object.
import copy
s_graph_cleaned = copy.deepcopy(fpm.s_graph)
edges = fpm.s_graph.graph.edges(data=True)
for edge in edges:
    hop_label = edge[2]["hop_label"]
    if hop_label != target_hop_label:
        s_graph_cleaned.break_edge(
            from_index=edge[0],
            to_index=edge[1],
            to_jimage=edge[2]["to_jimage"],
            allow_reverse=False,
        )
# Now find the dimension!
dimensionality = get_dimensionality_larsen(s_graph_cleaned)

# as an extra, we look at dimensionality when all equal-length and shorter pathways
# are included. So for this second approach we remove all pathways that are longer!
s_graph_cleaned = copy.deepcopy(fpm.s_graph)
edges = fpm.s_graph.graph.edges(data=True)
for edge in edges:
    # NOTE: there is a rounding error here. So we subtract 1e-5 from the length.
    # This ensures "hop_length > path.length" holds for cases where the rounding
    # increased the hop_length unintentially
    hop_length = edge[2]["hop"].length - 1e-6
    if hop_length > path.length:
        s_graph_cleaned.break_edge(
            from_index=edge[0],
            to_index=edge[1],
            to_jimage=edge[2]["to_jimage"],
            allow_reverse=False,
        )
# Now find the dimension when including shorter pathways!
dimensionality_cumlengths = get_dimensionality_larsen(s_graph_cleaned)

# --------------------------------------------------------------------------------------

# STAGE 6 -- Diffusing Ion's Change in Ewald Energy along the Pathway

# We run this within a supercell structure that is oxidation-state decorated
# See our utility function at the bottom of this file for more info.
supercell_path = get_oxi_supercell_path(path, min_sl_v=7, oxi=True)

# We use matminer's class to calculate the EwaldSiteEnergy to an accuracy of 
# 3 decimal places -- which is a quick and rough calculation.
from matminer.featurizers.site import EwaldSiteEnergy
ewaldcalculator = EwaldSiteEnergy(accuracy=3)

# We only look at 5 images along the pathway and we do a full idpp relaxation for
# the series of images.
images = supercell_path.get_structures(
    nimages=5,
    idpp=True,
)
# NOTE: the diffusion atom is always the first site in these structures (index=0)

ewald_energies = []
for image in images:
    ewald_energy = ewaldcalculator.featurize(image, 0)  # index=0 for diffusing atom
    ewald_energies.append(ewald_energy[0])

# We convert this list of ewald energies to be relative to the starting ewald energy
ewald_energies = [
    (e - ewald_energies[0]) / abs(ewald_energies[0]) for e in ewald_energies
]

# We want to store the maximum change in ewald energy, regardless of where it is
# at on this pathway.
delta_ee = max(ewald_energies)

# --------------------------------------------------------------------------------------

# STAGE 7 -- Diffusing Ion's Change in Ionic Radii Overlap along the Pathway

# We run this within a supercell structure that is oxidation-state decorated
# See our utility function at the bottom of this file for more info.
supercell_path = get_oxi_supercell_path(path, min_sl_v=7, oxi=True)

# We only look at 5 images along the pathway and we do a full idpp relaxation for
# the series of images.
images = supercell_path.get_structures(
    nimages=5,
    idpp=True,
)
# NOTE: the diffusion atom is always the first site in these structures (index=0)

# We now want to find the max change in anion, cation, and nuetral atom overlap.
# We start by collecting the overlaps at each point along the pathway. Also, note
# that "overlap" is effectively a measure of the "shortest bond distance" that
# is adjusted based on empirical ionic radii.
overlap_data_cations, overlap_data_anions = [], []
for image in images:
    # grab the diffusing ion. This is always index 0. Also grab it's radius
    moving_site = image[0]
    moiving_site_radius = moving_site.specie.ionic_radius
    # grab the diffusing ion's nearest neighbors within 8 angstroms and include
    # neighboring unitcells
    moving_site_neighbors = image.get_neighbors(
        moving_site,
        r=8.0,
        include_image=True,
    )
    # This is effectively our empty starting list. I set these to -999 to ensure
    # they are changed.
    max_overlap_cation, max_overlap_anion = (-999, -999)
    for neighbor, distance, _, _ in moving_site_neighbors:
        neighbor_radius = neighbor.specie.ionic_radius
        overlap = moiving_site_radius + neighbor_radius - distance
        # separate overlap analysis to oxidation types (+, -, or nuetral)
        if ("+" in neighbor.species_string) and (overlap > max_overlap_cation):
            max_overlap_cation = overlap
        elif ("-" in neighbor.species_string) and (overlap > max_overlap_anion):
            max_overlap_anion = overlap
        elif (
            ("-" not in neighbor.species_string)
            and ("+" not in neighbor.species_string)
        ):
            # the scenario of nuetral sites is ignored in this guide
            continue 
    overlap_data_cations.append(max_overlap_cation)
    overlap_data_anions.append(max_overlap_anion)
# We convert these values into ones relative to the starting image's overlap
overlap_data_cations_rel = [
    (image - overlap_data_cations[0]) for image in overlap_data_cations
]
overlap_data_anions_rel = [
    (image - overlap_data_anions[0]) for image in overlap_data_anions
]

# We want to store the maximum change in overlap, regardless of where it is
# at on this pathway. Note this can be negative.
ionic_radii_overlap_cations = max(overlap_data_cations_rel, key=abs)
ionic_radii_overlap_anions = max(overlap_data_anions_rel, key=abs)

# --------------------------------------------------------------------------------------

# STAGE 8 -- VASP Calculations (static + partial relaxation)

# We run this within a supercell structure that doesn't need to be oxidation-state
# decorated. See our utility function at the bottom of this file for more info.
# See the main text for what is used for min_sl_v
supercell_path = get_oxi_supercell_path(path, min_sl_v=10, oxi=False)

# We only look at 1 image along the pathway and we do a full idpp relaxation for
# the series of images. Thus, we only have the start, midpoint, and end structures.
images = path_supercell.get_structures(nimages=1, idpp=True)

# !!! NOTE: These structures serve as the inputs for the methods described below.
# Please refer to the main text for how NEB vs static calculations are performed
# as well as how settings vary accross these calculation types.

# For the parent input settings, we use MITRelaxSet when handling the start 
# and end images (and also the midpoint when it's a static calc). When doing a
# relaxation of the midpoint, we use MITNEBSet
from pymatgen.io.vasp.sets import MITRelaxSet, MITNEBSet
# These are the settings we've changed relative to the parent input set. Note
# these vary from calculation to calculation, so refer to the main text!
custom_incar = dict(
    NSW=0,  # see main text for varying values
    EDIFF=1.0e-05,  # see main text for varying values
    LDAU=False,  # Turns off +U setting for low-quality calcs (following MITNEBSet)
    ISIF=3, # Full relaxation of lattice and sites when NSW > 0
    EDIFFG=-0.1,  # see main text for varying values when NSW > 0
    IBRION=-1, # 2 for initial guess when NSW > 0 (following MITNEBSet)
    ISYM=0,  # Turn off symmetry
)
# as an example, we'd initilize MITRelaxSet for a single image like this
input_set = MITRelaxSet(image_structure, user_incar_settings=custom_incar)
# These files can be generated using...
# Note, Custodian (below) assumes that it runs in the current-working directory, so
# you will likely write your inputs in write_input(".")
vasp_input_set.write_input("/path/to/my/folder")

# We also want to initialize our input set with error handling, which is carried
# out by Custodian

# We use mimimal error handlers in our runs -- as this set is commonly used
# in the Materials Project MD runs (as seen in the Atomate code). Note that
# we don't use any validators when doing a midpoint NEB because of the differing
# file structure.
from custodian.vasp.handlers import VaspErrorHandler, NonConvergingErrorHandler
errorhandlers = [VaspErrorHandler(), NonConvergingErrorHandler()]
validators = [VasprunXMLValidator(), VaspFilesValidator()]

# The Job specification has a number of configuration options, were we only
# show the vasp command control here. Note, that these objects are provided
# to the Custodian class as "jobs" --> which is a list of job objects.
# We also show an example vasp command that uses parallelization accross 16 cores.
from custodian.vasp.jobs import VaspJob, VaspNEBJob
jobs = VaspJob(vasp_cmd="mpirun -n 16 vasp")

# now put all of the jobs and error handlers together. We don't want any failed
# jobs to hog resources by endlessly attempting fixes. So we limit the total
# number of attempts to 5
from custodian import Custodian
custodian = Custodian(
    errorhandlers,
    jobs,
    validators=validators,
    max_errors=5,
)
# you can not launch your job with error handling!
custodian.run()


# --------------------------------------------------------------------------------------

# Utility: Converting path object to an equivalent path with supercell

# In a number of the methods above, we need to convert a specific path to a given
# supercell size. The easiest option is to provide a supercell to the DistinctPathFinder
# class -- if you can do this, you should! However, in this study, we have a known
# pathway in the unitcell and we want to convert it to the same pathway in a supercell
# structure. To do this, we 
from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen_diffusion.neb.pathfinder import MigrationPath

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
