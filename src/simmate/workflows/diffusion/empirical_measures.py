# -*- coding: utf-8 -*-

"""

ETL (Extract, Transform, Load)
E = load pathway from sql database given id
T = run series of empirical analyses to get data
L = add empirical data to SQL database

Example of running the code below:
    pathway_id = 1
    e = load_pathway_from_db(pathway_id)
    t = get_empirical_measures(e)
    l = add_empiricalmeasures_to_db(pathway_id, t)

"""

import json
import numpy


from pymatgen.core.structure import Structure

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

from prefect import Flow, Parameter, task

# --------------------------------------------------------------------------------------


# TODO: This is just a repeat of other code. Move this to a module for reuse.
# @task
def load_structure_from_db(structure_id):

    from simmate.configuration import manage_django  # ensures setup
    from simmate.database.all import Structure as Structure_DB

    # grab the proper Structure entry and we want only the structure column
    # This query is ugly to read so here's the breakdown:
    #   .values_list("structure", flat=True) --> only grab the structure column
    #   .get(id=structure_id) --> grab the structure by row id (or personal key)
    #   ['structure'] --> the query gives us a dict where we just want this key's value
    structure_json = Structure_DB.objects.values_list(
        "structure",
        flat=True,
    ).get(id=structure_id)

    # convert the output from a json string to python dictionary
    structure_dict = json.loads(structure_json)
    # convert the output from a dictionary to pymatgen Structure object
    structure = Structure.from_dict(structure_dict)

    return structure


@task
def load_pathway_from_db(pathway_id):

    from simmate.configuration import manage_django  # ensures setup
    from simmate.database.all import Pathway as Pathway_DB

    # grab the pathway object
    pathway_db = Pathway_DB.objects.get(id=pathway_id)

    # grab the related structure as a pymatgen object
    structure = load_structure_from_db(pathway_db.structure_id)

    # Use pymatgen diffusion to identify all paths
    # TODO: I just hardcode my options here, but in the future, I can have this task
    # accept some kwargs to pass DistinctPathFinder
    dpf = DistinctPathFinder(
        structure=structure,
        migrating_specie="F",
        max_path_length=5,
        symprec=0.1,
        perc_mode=None,
    )

    # grab all the paths as MigrationPath objects
    paths = dpf.get_paths()

    # Go to the proper index and make sure the pathways match
    path = paths[pathway_db.dpf_index]
    assert path.length == pathway_db.distance
    assert (
        path.isite.frac_coords
        == numpy.fromstring(pathway_db.isite, dtype=float, sep=" ")
    ).all()
    assert (
        path.msite.frac_coords
        == numpy.fromstring(pathway_db.msite, dtype=float, sep=" ")
    ).all()
    assert (
        path.esite.frac_coords
        == numpy.fromstring(pathway_db.esite, dtype=float, sep=" ")
    ).all()

    # TODO: This code should be located elsewhere, but I just grab this info
    # for convience. This should grabbed in a separate "extract" task.
    shortest_path_length = paths[0].length

    # if the pathways match, then we can return the pathway object!
    return structure, path, shortest_path_length


# --------------------------------------------------------------------------------------


@task
def get_empirical_measures(pathway_data):

    # TODO: format this better with prefect
    structure, path, shortest_path_length = pathway_data

    # TODO: I can break this task down to run in parallel and also move code to lower
    # levels.

    # BUG: path.iindex doesn't give the site index, but the index for the wykoff list
    # Therefore, I need to figure out the path index, myself
    # TODO: This may be worth storing in the pathway database table
    for iindex, site in enumerate(structure):
        if path.isite == site:
            # we break here with the propper iindex
            break
        # BUG: if match is not found, the final index will be returned, which
        # isn't caught

    # grab the unitcell structure
    # structure = path.symm_structure

    # grab the total number of sites in the structure unitcell and supercell sizes
    nsites_unitcell = structure.num_sites
    # iterate through supercell sizes and grab the nsites for each
    min_superlattice_vectors = [7, 10, 12]
    nsites_supercells = []
    for min_sl_v in min_superlattice_vectors:
        supercell = structure.copy()
        supercell_size = [
            (min_sl_v // length) + 1 for length in supercell.lattice.lengths
        ]
        supercell.make_supercell(supercell_size)
        nsites_supercells.append(supercell.num_sites)
    nsites_888, nsites_101010, nsites_121212 = nsites_supercells

    # atomic fraction of the diffusion ion
    atomic_fraction = structure.composition.get_atomic_fraction("F")

    # Distance of the pathway relative to the shortest pathway distance
    # in the structure using the formula: (D - Dmin)/Dmin
    distance_rel_min = (path.length - shortest_path_length) / shortest_path_length

    # # predicted oxidation state of the diffusing ion based on bond valence
    # structure.add_oxidation_state_by_guess() # ALTERNATIVE OXIDATION
    oxidation_check = ValenceIonicRadiusEvaluator(structure)
    oxidation_state = oxidation_check.structure[iindex].specie.oxi_state

    # TODO: all of these below should be their own workflow tasks instead of
    # try/except like shown below.

    # Dimensionality of an individual pathway based on the Larsen Method
    try:
        dimensionality, dimensionality_cumlengths = get_path_dimension(structure, path)
    except:
        dimensionality, dimensionality_cumlengths = (None, None)

    # relative change in ewald_energy along the pathway: (Emax-Estart)/Estart
    try:
        ewald_energy = get_ewald_energy(structure, path)
    except:
        ewald_energy = None

    # relative change in ionic radii overlaps: (Rmax-Rstart)/Rstart
    try:
        (
            ionic_radii_overlap_cations,
            ionic_radii_overlap_anions,
        ) = get_ionic_radii_overlap(structure, path)
    except:
        ionic_radii_overlap_cations, ionic_radii_overlap_anions = (None, None)

    # return all of the data we grabbed as a dictionary
    return dict(
        nsites_unitcell=nsites_unitcell,
        nsites_888=nsites_888,
        nsites_101010=nsites_101010,
        nsites_121212=nsites_121212,
        atomic_fraction=atomic_fraction,
        distance_rel_min=distance_rel_min,
        oxidation_state=oxidation_state,
        dimensionality=dimensionality,
        dimensionality_cumlengths=dimensionality_cumlengths,
        ewald_energy=ewald_energy,
        ionic_radii_overlap_cations=ionic_radii_overlap_cations,
        ionic_radii_overlap_anions=ionic_radii_overlap_anions,
    )


# --------------------------------------------------------------------------------------

# NOTE: if an entry already exists for this pathway, it is overwritten


@task
def add_empiricalmeasures_to_db(pathway_id, em_dict):

    from simmate.configuration import manage_django  # ensures setup
    from simmate.database.all import EmpiricalMeasures as EM_DB, Pathway as Pathway_DB

    # grab the proper Pathway entry
    # OPTIMIZE: will this function still work if I only grab the id value?
    pathway_db = Pathway_DB.objects.get(id=pathway_id)

    # now add the empirical data using the supplied dictionary
    em_data = EM_DB(status="C", pathway=pathway_db, **em_dict)
    em_data.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("GenerateEmpiricalMeasuresforPathway") as workflow:

    # load the structure object from our database
    pathway_id = Parameter("pathway_id")

    # load the pathway object from our database
    # TODO: I load more than just the path object for now
    pathway_data = load_pathway_from_db(pathway_id)

    # calculate all of the empirical data
    em_data = get_empirical_measures(pathway_data)

    # save the data to our database
    add_empiricalmeasures_to_db(pathway_id, em_data)

# --------------------------------------------------------------------------------------
