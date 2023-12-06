#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 11:30:31 2023

@author: sweav
"""

from pymatgen.core import Structure
from pathlib import Path
from simmate.apps.warrenapp.outputs.elfcar import Elfcar
from pymatgen.analysis.graphs import StructureGraph
from simmate.apps.warrenapp.badelf_tools.badelf_algorithm_functions import (   
    get_voxel_from_index,
    get_voxel_from_neigh,
    get_partitioning_line,
    get_50_neighbors
    )
from pymatgen.analysis.dimensionality import get_dimensionality_larsen


def get_electride_dimensionality(
        directory: Path,
        empty_structure: Structure = None,
        empty_file: str = "POSCAR_empty",
        electride_elfcar: Elfcar = None,
        electride_elfcar_file: str = "ELFCAR_e"
        ):
    #read in structure and remove all atoms except dummy electride sites
    if empty_structure is None:
        structure = Structure.from_file(directory / empty_file)
    else:
        structure = empty_structure.copy()
    species = list(structure.symbol_set)
    species.remove("He")
    structure.remove_species(species)
    
    #read in elfcar and change its structure to the one containing only electrides.
    #get the lattice dictionary from the elfcar
    if electride_elfcar is None:
        elfcar = Elfcar.from_file(directory / electride_elfcar_file)
    else:
        elfcar = electride_elfcar.copy()
    elfcar.structure = structure
    lattice = elfcar.get_lattice_from_elfcar()
    
    # get the grid from the elfcar
    grid = elfcar.data["total"]
    
    # get the 50 nearest electride neighbors. We only do this because we need to make
    # sure that electride sites that are very far away are thoroughly checked
    nearest_neighbors = get_50_neighbors(structure)
    
    # create an empty StructureGraph object. This maps connections between different
    # atoms, including those across unit cell boundaries. We will fill this out using
    # the list of neighbors we just defined.
    graph = StructureGraph.with_empty_graph(structure)
    
    #iterate over each unique electride site.
    for index, neighbors in enumerate(nearest_neighbors):
        # get the voxel coords for the electride site
        site_pos = get_voxel_from_index(index, lattice)
        
        # loop over the neighboring electride sites
        for neighbor in neighbors:
            # We will have many excess electride sites that are in unit cells that
            # don't border the one we're looking at. I'm not certain, but I don't
            # think those are necessary. We cut them out here to save time from the
            # get_partitioning_line function.
            
            # Assume this neighbor is not more than one unit cell away
            more_than_1_unit_cell_away = False
            for integer in neighbor.image:
                # Check if an integer other than -1, 1, or 0 is present. This indicates
                # we've been transformed more than one unit cell away.
                if integer not in [-1,0,1]:
                    more_than_1_unit_cell_away = True
                    break
            # Check if we've moved more than one unit cell away. If we have, skip
            # to the next neighbor
            if more_than_1_unit_cell_away:
                continue
            
            # get the voxel coord for the connected electride site and get the ELF
            # line between the site and this neighbor
            neigh_pos = get_voxel_from_neigh(neighbor, lattice)
            pos, values = get_partitioning_line(site_pos, neigh_pos, grid)
            
            # If a 0 is not found in the elf line these sites are connected and we
            # want to add an edge to our graph.
            if 0 not in values:
                graph.add_edge(
                    from_index=index, # The site index of the electride site of interest
                    from_jimage=(0, 0, 0), # The image the electride site is in. Always (0,0,0)
                    to_index=neighbor.index, # The neighboring electrides site index
                    to_jimage=neighbor.image, # The image that the neighbor is in.
                    weight=None, # The relative weight of the neighbor. We ignore this.
                    edge_properties=None,
                    warn_duplicates=False, # Duplicates are fine for us.
                    )
    
    # Get the dimensionality from our StructureGraph. If more than one group of electrides
    # is found, it will default to the highest dimensionality.
    return get_dimensionality_larsen(graph)
