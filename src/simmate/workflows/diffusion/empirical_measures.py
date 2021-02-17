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
import copy
import numpy

from matminer.featurizers.site import EwaldSiteEnergy

from pymatgen.core.structure import Structure
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator
from pymatgen.analysis.dimensionality import get_dimensionality_larsen

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder
from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper

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

# TODO: consider moving this to an "extract" task
def get_oxi_supercell_path(structure, path, min_sl_v):

    # if desired, add oxidation states to structure
    structure = ValenceIonicRadiusEvaluator(structure).structure

    # make the supercell
    supercell = structure.copy()
    supercell_size = [(min_sl_v // length) + 1 for length in supercell.lattice.lengths]
    supercell.make_supercell(supercell_size)

    # run the pathway analysis using the supercell structure
    dpf = DistinctPathFinder(
        structure=supercell,
        migrating_specie="F-",
        max_path_length=path.length + 1e-5,  # add extra for rounding errors
        symprec=0.1,
        perc_mode=None,
    )

    # go through paths until we find a match
    # assume we didn't find a match until proven otherwise
    found_match = False
    for path_check in dpf.get_paths():
        if (
            abs(path.length - path_check.length) <= 1e-5  # capture rounding error
            and path.iindex == path_check.iindex
            and path.eindex == path_check.eindex
        ):
            # we found a match so break. No need to check any other pathways.
            found_match = True
            break

    # Just in case we didn't find a match, we need to raise an error
    if not found_match:
        raise Exception("Failed to find the equivalent pathway in the supercell")

    # we now have path_check as the equivalent pathway. This is what the user
    # wants so we can return it
    return path_check


# BUG: This code will change drastically b/c the FullPathMapper function looks
# to be under full development.
def get_path_dimension(structure, path):

    fpm = FullPathMapper(
        structure,
        "F",
        # plus small number to ensure we get the paths
        max_path_length=path.length + 1e-5,
    )

    # we have to do this ourselves (FullPathMapper was written by a beginner)
    fpm.populate_edges_with_migration_paths()
    fpm.group_and_label_hops()
    fpm.get_unique_hops_dict()

    # For testing -- if you need a list of all edge hop labels
    # edge_labels = numpy.array(
    #     [d["hop_label"] for u, v, d in fpm.s_graph.graph.edges(data=True)]
    # )

    # I need to figure out the correct hop label and I do this by looking
    # at all of them until I have a "graph edge" that matches my pathway
    edges = fpm.s_graph.graph.edges(data=True)
    for edge in edges:
        if path == edge[2]["hop"]:
            target_hop_label = edge[2]["hop_label"]
            break
    # BUG: if a match is never found, we never set target_hop_label and the code
    # below will exit with an error

    # Delete all but a specific MigrationPath (which has a unique
    # 'hop-label')
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
    # These are other methods of breaking graph edges that I ended up not using
    # fpm.s_graph.break_edge(from_index, to_index, to_jimage=None, allow_reverse=False)
    # fpm.s_graph.graph.remove_edge(0,0)

    # For testing -- if you need a list of all edge hop labels AFTER deleting
    # edge_labels_test = numpy.array(
    #     [d["hop_label"] for u, v, d in s_graph_test.graph.edges(data=True)]
    # )

    dimensionality = get_dimensionality_larsen(s_graph_cleaned)

    # ------------------------------------------------------------------------

    # as an extra, I look at dimensionality_cumlengths as well
    # I delete edges here only if they are longer than the one provided
    s_graph_cleaned = copy.deepcopy(fpm.s_graph)
    edges = fpm.s_graph.graph.edges(data=True)
    for edge in edges:
        hop_length = edge[2]["hop"].length
        if hop_length > path.length:
            s_graph_cleaned.break_edge(
                from_index=edge[0],
                to_index=edge[1],
                to_jimage=edge[2]["to_jimage"],
                allow_reverse=False,
            )
    dimensionality_cumlengths = get_dimensionality_larsen(s_graph_cleaned)

    return dimensionality, dimensionality_cumlengths


def get_ewald_energy(structure, path):

    # Let's run this within a supercell structure
    supercell_path = get_oxi_supercell_path(
        structure,
        path,
        min_sl_v=7,
    )

    ewaldcalculator = EwaldSiteEnergy(accuracy=3)  # 12 is default
    # NOTE: requires oxidation state decorated structure

    images = supercell_path.get_structures(
        nimages=5,
        # vac_mode=True,  # vacancy mode
        idpp=True,
        # **idpp_kwargs,
        # species = 'Li', # Default is None. Set this if I only want one to move
    )
    # NOTE: the diffusion atom is always the first site in these structures (index=0)

    ewald_energies = []
    for image in images:
        ewald_energy = ewaldcalculator.featurize(image, 0)  # index=0 for diffusing atom
        ewald_energies.append(ewald_energy[0])  # [0] becuase its given within a list

    # I convert this list of ewald energies to be relative to the start energy
    ewald_energies = [
        (e - ewald_energies[0]) / abs(ewald_energies[0]) for e in ewald_energies
    ]

    # I want to store the maximum change in ewald energy, so I just store the max
    return max(ewald_energies)


def get_ionic_radii_overlap(structure, path):

    # Let's run this within a supercell structure
    supercell_path = get_oxi_supercell_path(
        structure,
        path,
        min_sl_v=7,
    )

    # let's grab all of the pathway images
    images = supercell_path.get_structures(
        nimages=5,
        # vac_mode=True,  # vacancy mode
        idpp=True,
        # **idpp_kwargs,
        # species = 'Li', # Default is None. Set this if I only want one to move
    )
    # NOTE: the diffusion atom is always the first site in these structures (index=0)

    # Finding max change in anion, cation, and nuetral atom overlap
    overlap_data_cations, overlap_data_anions, overlap_data_nuetral = [], [], []

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

        # This is effective our empty starting list. I set these to -999 to ensure
        # they are changed.
        max_overlap_cation, max_overlap_anion, max_overlap_nuetral = (
            -999,
            -999,
            -999,
        )
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
                and (overlap > max_overlap_nuetral)
            ):
                max_overlap_nuetral = overlap
        overlap_data_cations.append(max_overlap_cation)
        overlap_data_anions.append(max_overlap_anion)
        overlap_data_nuetral.append(max_overlap_nuetral)
    # make lists into relative values
    # TODO: consider using /abs(overlap_data_cations[0]) instead
    overlap_data_cations_rel = [
        (image - overlap_data_cations[0]) for image in overlap_data_cations
    ]
    overlap_data_anions_rel = [
        (image - overlap_data_anions[0]) for image in overlap_data_anions
    ]
    overlap_data_nuetral_rel = [
        (image - overlap_data_nuetral[0]) for image in overlap_data_nuetral
    ]

    # grab the maximum deviation from 0. Note this can be negative!
    ionic_radii_overlap_cations = max(overlap_data_cations_rel, key=abs)
    ionic_radii_overlap_anions = max(overlap_data_anions_rel, key=abs)
    ionic_radii_overlap_nuetral = max(overlap_data_nuetral_rel, key=abs)

    return (
        ionic_radii_overlap_cations,
        ionic_radii_overlap_anions,
        # ionic_radii_overlap_nuetral,
    )


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

    # # Dimensionality of an individual pathway based on the Larsen Method
    dimensionality, dimensionality_cumlengths = get_path_dimension(structure, path)

    # # relative change in ewald_energy along the pathway: (Emax-Estart)/Estart
    ewald_energy = get_ewald_energy(structure, path)

    # # relative change in ionic radii overlaps: (Rmax-Rstart)/Rstart
    ionic_radii_overlap_cations, ionic_radii_overlap_anions = get_ionic_radii_overlap(
        structure, path
    )

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
