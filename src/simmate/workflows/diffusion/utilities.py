# -*- coding: utf-8 -*-

import copy

from pymatgen.core.sites import PeriodicSite
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator
from pymatgen.analysis.dimensionality import get_dimensionality_larsen

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder, MigrationPath
from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper

from matminer.featurizers.site import EwaldSiteEnergy

# --------------------------------------------------------------------------------------


def get_oxi_supercell_path(path, min_sl_v):

    # add oxidation states to structure
    structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure

    structure_supercell = structure.copy()
    supercell_size = [
        (min_sl_v // length) + 1 for length in structure_supercell.lattice.lengths
    ]
    structure_supercell.make_supercell(supercell_size)

    isite_new = PeriodicSite(
        species=path.isite.specie,
        coords=path.isite.coords,
        coords_are_cartesian=True,
        lattice=structure_supercell.lattice,
    )
    esite_new = PeriodicSite(
        species=path.esite.specie,
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


def get_oxi_supercell_path_OLD(structure, path, min_sl_v):

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


# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------
