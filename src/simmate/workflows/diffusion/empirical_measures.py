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

import copy

from prefect import Flow, Parameter, task
from prefect.triggers import all_finished
from prefect.storage import Local as LocalStorage
from prefect.executors import DaskExecutor

from pymatgen.analysis.dimensionality import get_dimensionality_larsen
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator

from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper

from matminer.featurizers.site import EwaldSiteEnergy

from simmate.workflows.diffusion.utilities import get_oxi_supercell_path

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


# --------------------------------------------------------------------------------------


@task
def get_oxidation_state(path):

    # run oxidation analysis on structure
    structure = ValenceIonicRadiusEvaluator(path.symm_structure).structure

    # grab the oxidation state of the diffusion ion
    specie = structure[path.iindex].specie.oxi_state

    return specie


# --------------------------------------------------------------------------------------

# BUG: This code will change drastically b/c the FullPathMapper function looks
# to be under full development.
@task
def get_path_dimension(path):

    fpm = FullPathMapper(
        path.symm_structure,
        path.isite.specie,
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

    # ----------------------------

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


@task
def get_ewald_energy(path):

    # Let's run this within a supercell structure
    supercell_path = get_oxi_supercell_path(path, min_sl_v=7, oxi=True)

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


@task
def get_ionic_radii_overlap(path):

    # Let's run this within a supercell structure
    supercell_path = get_oxi_supercell_path(path, min_sl_v=7, oxi=True)

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
    # overlap_data_nuetral_rel = [
    #     (image - overlap_data_nuetral[0]) for image in overlap_data_nuetral
    # ]

    # grab the maximum deviation from 0. Note this can be negative!
    ionic_radii_overlap_cations = max(overlap_data_cations_rel, key=abs)
    ionic_radii_overlap_anions = max(overlap_data_anions_rel, key=abs)
    # ionic_radii_overlap_nuetral = max(overlap_data_nuetral_rel, key=abs)

    return (
        ionic_radii_overlap_cations,
        ionic_radii_overlap_anions,
        # ionic_radii_overlap_nuetral,
    )


# --------------------------------------------------------------------------------------

# NOTE: if an entry already exists for this pathway, it is overwritten


@task(trigger=all_finished)
def add_empiricalmeasures_to_db(
    pathway_id, oxi_data, dimension_data, ewald_data, iro_data
):

    from simmate.configuration import django  # ensures setup
    from simmate.database.diffusion import EmpiricalMeasures as EM_DB

    # now add the empirical data using the supplied dictionary
    # NOTE: the "if not __ else None" code is to make sure there wasn't an error
    # raise in one of the upstream tasks. For example there was an error, oxi_data
    # would be an excpetion class -- in that case, we choose to store None instead
    # of the exception itself.
    em_data = EM_DB(
        status="C",
        pathway_id=pathway_id,
        #
        oxidation_state=oxi_data if not isinstance(oxi_data, Exception) else None,
        #
        dimensionality=dimension_data[0]
        if not isinstance(dimension_data, Exception)
        else None,
        #
        dimensionality_cumlengths=dimension_data[1]
        if not isinstance(dimension_data, Exception)
        else None,
        #
        ewald_energy=ewald_data if not isinstance(ewald_data, Exception) else None,
        #
        ionic_radii_overlap_cations=iro_data[0]
        if not isinstance(iro_data, Exception)
        else None,
        #
        ionic_radii_overlap_anions=iro_data[1]
        if not isinstance(iro_data, Exception)
        else None,
    )
    em_data.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("Empirical Measures for Pathway") as workflow:

    # load the structure object from our database
    pathway_id = Parameter("pathway_id")

    # load the pathway object from our database
    # TODO: I load more than just the path object for now
    pathway = load_pathway_from_db(pathway_id)

    # calculate all of the empirical data
    oxi_data = get_oxidation_state(pathway)
    dimension_data = get_path_dimension(pathway)
    ewald_data = get_ewald_energy(pathway)
    iro_data = get_ionic_radii_overlap(pathway)

    # save the data to our database
    add_empiricalmeasures_to_db(
        pathway_id, oxi_data, dimension_data, ewald_data, iro_data
    )

# for Prefect Cloud compatibility, set the storage to a an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

# set the executor to a locally ran executor
workflow.executor = DaskExecutor(address="tcp://160.0.0.15:38875")

# --------------------------------------------------------------------------------------
