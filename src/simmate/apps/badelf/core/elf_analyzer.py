#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import math
import warnings
from functools import cached_property
from pathlib import Path

import networkx
import numpy as np
import plotly.graph_objects as go
import psutil
from networkx import DiGraph
from networkx.utils import UnionFind
from numpy.typing import NDArray
from pymatgen.analysis.local_env import CrystalNN
from scipy.ndimage import label

from simmate.apps.bader.toolkit import Grid
from simmate.toolkit import Structure
from simmate.apps.badelf.core.partitioning import PartitioningToolkit


class BifurcationGraph(DiGraph):
    """
    This is an expansion of networkx's Graph class specifically with
    additional methods related to bifurcation plots.
    """

    def parent_index(self, n: int) -> int:
        """
        Returns the node index for the parent of the provided node index
        """
        predecessor_list = list(self.predecessors(n))
        if len(predecessor_list) > 0:
            return predecessor_list[0]
        else:
            return None

    def parent_dict(self, n: int) -> dict:
        """
        Returns the dictionary of attributes assigned to the parent of
        the provided node index
        """
        parent_index = self.parent_index(n)
        if parent_index is not None:
            return self.nodes[parent_index]
        else:
            return None

    def child_indices(self, n: int) -> NDArray[np.int64]:
        """
        Returns the indices of the children of this node if they exist
        """
        child_indices_list = list(self.successors(n))
        return np.array(child_indices_list)

    def child_dicts(self, n: int) -> dict:
        """
        Returns the dictionaries of attributes assigned to the children of
        the provided node index. Returns a nested dict with child indices
        as keys and dicts as values.
        """
        children = {}
        for i in self.child_indices(n):
            children[i] = self.nodes[i]
        return children

    def deep_child_indices(self, n: int) -> NDArray[np.int64]:
        """
        Returns the indices of all subsequent nodes after this node.
        """
        all_found = False
        child_indices = self.child_indices(n)
        while not all_found:
            new_child_indices = child_indices.copy()
            for i in child_indices:
                new_child_indices = np.concatenate(
                    [new_child_indices, self.child_indices(i)]
                )
            new_child_indices = np.unique(new_child_indices)
            if len(child_indices) == len(new_child_indices):
                all_found = True
            child_indices = new_child_indices
        return child_indices.astype(int)

    def deep_child_dicts(self, n: int) -> dict:
        """
        Returns the dictionaries of attributes assigned subsequent nodes
        after this node. Returns a nested dict with child indices
        as keys and dicts as values.
        """
        children = {}
        for i in self.deep_child_indices(n):
            children[i] = self.nodes[i]
        return children

    def sibling_indices(self, n: int) -> NDArray[np.int64]:
        """
        Returns the indices of the siblings of this node if they exist
        """
        parent_idx = self.parent_index(n)
        if parent_idx is None:
            return
        siblings = self.child_indices(parent_idx)
        # remove self
        siblings = siblings[siblings != n]
        return siblings

    def sibling_dicts(self, n: int) -> dict:
        """
        Returns the dictionaries of attributes assigned to the siblings of
        the provided node index. Returns a nested dict with child indices
        as keys and dicts as values.
        """
        siblings = {}
        for i in self.sibling_indices(n):
            siblings[i] = self.nodes[i]
        return siblings


class ElfAnalyzerToolkit:
    """
    A class for finding electride sites from an ELFCAR.

    Args:
        grid : Grid
            A BadELF app Grid instance made from an ELFCAR.

        directory : Path
            Path the the directory to write files from
    """

    def __init__(
        self,
        elf_grid: Grid,
        charge_grid: Grid,
        directory: Path,
        separate_spin: bool = False,
        ignore_low_pseudopotentials: bool = False,
    ):
        self.elf_grid = elf_grid.copy()
        self.charge_grid = charge_grid.copy()
        self.directory = directory
        self.ignore_low_pseudopotentials = ignore_low_pseudopotentials
        self._basin_labeled_voxels = None
        # check if this is a spin polarized calculation and if the user wants
        # to pay attention to this.
        if elf_grid.is_spin_polarized and separate_spin:
            self.spin_polarized = True
            self._elf_grid_up, self._elf_grid_down = elf_grid.split_to_spin()
            self._charge_grid_up, self._charge_grid_down = charge_grid.split_to_spin(
                "charge"
            )
        else:
            self.spin_polarized = False
            self._elf_grid_up, self._elf_grid_down = None, None
            self._charge_grid_up, self._charge_grid_down = None, None

    @property
    def structure(self) -> Structure:
        """
        Shortcut to grid's structure object
        """
        structure = self.elf_grid.structure.copy()
        structure.add_oxidation_state_by_guess()
        return structure

    @cached_property
    def atom_coordination_envs(self) -> list:
        """
        Gets the coordination environment for the atoms in the system
        using CrystalNN
        """
        cnn = CrystalNN()
        neighbors = cnn.get_all_nn_info(self.structure)
        return neighbors

    @staticmethod
    def get_shared_feature_neighbors(structure: Structure) -> NDArray:
        """
        For each covalent bond or metallic feature in a dummy atom labeled
        structure, returns a list of nearest atom neighbors.
        """
        # We want to get the atoms and electride sites that are closest to each
        # shared feature. However, we don't want to find any nearby shared features
        # as neighbors.
        # To do this we will remove all of the shared dummy atoms, and create
        # temporary structures with only one of the shared dummy atoms at a time.
        shared_feature_indices = []
        cleaned_structure = structure.copy()
        for symbol in ["Z", "M", "Le", "Lp"]:
            if not symbol in cleaned_structure.symbol_set:
                continue
            cleaned_structure.remove_species([symbol])
            shared_feature_indices.extend(structure.indices_from_symbol(symbol))
        shared_feature_indices = np.array(shared_feature_indices)
        shared_feature_indices.sort()
        # We will be using the indices of the cleaned structure to note neighbors,
        # so these must match the original structure. We assert that here
        assert all(
            cleaned_structure[i].species == structure[i].species
            for i in range(len(cleaned_structure))
        ), "Provided structure must list atoms and electride dummy atoms first"

        # Replace any electrides with "He" so that CrystalNN doesn't throw an error
        if "E" in cleaned_structure.symbol_set:
            cleaned_structure.replace_species({"E": "He"})
        # for each index, we append a dummy atom ("He" because its relatively small)
        # then get the nearest neighbors
        cnn = CrystalNN()
        all_neighbors = []
        for idx in shared_feature_indices:
            neigh_indices = []
            # Add this dummy atom to the temporary structure
            frac_coords = structure[idx].frac_coords
            temp_structure = cleaned_structure.copy()
            temp_structure.append("He", frac_coords)
            # Get the nearest neighbors to this dummy atom
            nn = cnn.get_nn(temp_structure, -1)
            # Get the index for each neighboras a list, then append this list
            # to our full list. Note that it is important that these indices be
            # the same as in the original structure, so atoms and electrides must
            # come before shared electrons in the provided structure.
            for n in nn:
                neigh_indices.append(n.index)
            all_neighbors.append(neigh_indices)
        return all_neighbors

    def get_atom_en_diff_and_cn(self, site: int) -> list([float, int]):
        """
        Uses the coordination environment of an atom to get the EN diff
        between it and it's neighbors as well as its coordination number.
        This is useful for guessing which radius to use.
        """
        # get the neighbors for this site and its electronegativity
        neigh_list = self.atom_coordination_envs[site]
        site_en = self.structure.species[site].X
        # create a variable for storing the largest EN difference
        max_en_diff = 0
        for neigh_dict in neigh_list:
            # get the EN for each neighbor and calculate the difference
            neigh_site = neigh_dict["site_index"]
            neigh_en = self.structure.species[neigh_site].X
            en_diff = site_en - neigh_en
            # if the difference is larger than the current stored one, replace
            # it.
            if abs(en_diff) > max_en_diff:
                max_en_diff = en_diff
        # return the en difference and number of neighbors
        return max_en_diff, len(neigh_list)

    def get_atom_radius_guess(self, site: int) -> float:
        atom_element = self.structure.species[site].element
        en_diff, neigh_num = self.get_atom_en_diff_and_cn(site)
        # The cutoff we use for ionic vs. covalent is arbitrary. It would be
        # worthwile to study a range of EN differences and see where covalent
        # bonds start to show up.
        ionic_en_cutoff = 1.6
        if abs(en_diff) < ionic_en_cutoff:
            # use covalent radius
            radius = atom_element.atomic_radius
        else:
            # use average ionic radius. We can guess if the atom is cationic
            # vs anionic using the EN difference. EN diff will be positive if
            # site is more EN than neighbors, meaning its an anion.
            if en_diff > 0:
                radius = atom_element.average_anionic_radius
            else:
                radius = atom_element.average_cationic_radius
        return radius

    @property
    def site_voxel_coords(self) -> np.array:
        frac_coords = self.structure.frac_coords
        vox_coords = self.elf_grid.get_voxel_coords_from_frac_full_array(frac_coords)
        return vox_coords.astype(int)

    @cached_property
    def site_sphere_voxel_coords(self) -> list:
        site_sphere_coords = []
        for vox_coord in self.site_voxel_coords:
            nearby_voxels = self.elf_grid.get_voxels_in_radius(0.1, vox_coord)
            site_sphere_coords.append(nearby_voxels)
        return site_sphere_coords

    @cached_property
    def bader_up(self):
        """
        Returns a completed pybader object
        """
        threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        if self.spin_polarized:
            return self._elf_grid_up.run_pybader(threads)
        else:
            return self.elf_grid.run_pybader(threads)

    @cached_property
    def bader_down(self):
        """
        Returns a completed pybader object
        """
        threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        if self.spin_polarized:
            return self._elf_grid_down.run_pybader(threads)
        else:
            return None

    def wrap_labeled_grid(self, labeled_grid: np.array):
        """
        Takes a 3D numpy array with labels and combines any that would
        connect if wrapped around the unit cell
        """
        label_structure = np.ones([3, 3, 3])

        # Features connected through opposite sides of the unit cell should
        # have the same label, but they don't currently. To handle this, we
        # pad our featured grid, re-label it, and check if the new labels
        # contain multiple of our previous labels.
        padded_featured_grid = np.pad(labeled_grid, 1, "wrap")
        relabeled_grid, label_num = label(padded_featured_grid, label_structure)

        connections = UnionFind()
        for i in range(label_num):
            mask = relabeled_grid == i
            connected_features = np.unique(padded_featured_grid[mask])
            for feature in connected_features[1:]:
                connections.union(connected_features[0], feature)
        # Get the sets of basins that are connected to each other
        connection_sets = list(connections.to_sets())
        for label_set in connection_sets:
            label_set = np.array(list(label_set))
            # replace all of these labels with the lowest one
            labeled_grid = np.where(
                np.isin(labeled_grid, label_set),
                label_set[0],
                labeled_grid,
            )
        # Now we reduce the feature labels so that they start at 0
        for i, j in enumerate(np.unique(labeled_grid)):
            labeled_grid = np.where(labeled_grid == j, i, labeled_grid)

        return labeled_grid

    def get_atoms_in_volume(self, volume_mask):
        """
        Checks if an atom is within this volume. This only checks the
        area immediately around the atom, so outer core basins may not
        be caught by this.
        """
        atom_values = []
        for atom_idx, atom_sphere_coords in enumerate(self.site_sphere_voxel_coords):
            atom_sphere_in_feature = np.where(
                volume_mask[
                    atom_sphere_coords[:, 0],
                    atom_sphere_coords[:, 1],
                    atom_sphere_coords[:, 2],
                ]
            )[0]
            if len(atom_sphere_in_feature) > 0:
                atom_values.append(atom_idx)
        return atom_values

    def get_atoms_surrounded_by_volume(self, mask):
        """
        Checks if a list of basins completely surround any of the atoms
        in the structure. This method uses scipy's ndimage package to
        label features in the grid combined with a supercell to check
        if atoms identical through translation are connected.
        """
        # first we get any atoms that are within the mask itself. These won't be
        # found otherwise because they will always sit in unlabeled regions.
        init_atoms = self.get_atoms_in_volume(mask)
        # Now we create a supercell of the mask so we can check connections to
        # neighboring cells. This will be used to check if the feature connects
        # to itself in each direction
        supercell_mask = self.elf_grid.get_2x_supercell(mask)
        # We also get an inversion of this mask. This will be used to check if
        # the mask surrounds each atom.
        inverted_mask = supercell_mask == False
        # Now we use use scipy to label unique features in our masks
        structure = np.ones([3, 3, 3])
        feature_supercell, _ = label(supercell_mask, structure)
        inverted_feature_supercell, _ = label(inverted_mask, structure)
        # if an atom was fully surrounded, it should sit inside one of our labels.
        # The same atom in an adjacent unit cell should have a different label.
        # To check this, we need to look at the atom in each section of the supercell
        # and see if it has a different label in each.
        # Similarly, if the feature is disconnected from itself in each unit cell
        # any voxel in the feature should have different labels in each section.
        # If not, the feature is connected to itself in multiple directions and
        # must surround many atoms.
        transformations = np.array(
            [
                [0, 0, 0],  # -
                [1, 0, 0],  # x
                [0, 1, 0],  # y
                [0, 0, 1],  # z
                [1, 1, 0],  # xy
                [1, 0, 1],  # xz
                [0, 1, 1],  # yz
                [1, 1, 1],  # xyz
            ]
        )
        # First we check for feature connectivity. We use the first coordinate
        feat_vox_coords = np.argwhere(mask)[0]
        # convert to frac_coords
        feat_frac_coords = self.elf_grid.get_frac_coords_from_vox(feat_vox_coords)
        transformed_coords = transformations + feat_frac_coords
        voxel_coords = self.elf_grid.get_voxel_coords_from_frac_full_array(
            transformed_coords
        ).astype(int)
        features = feature_supercell[
            voxel_coords[:, 0], voxel_coords[:, 1], voxel_coords[:, 2]
        ]
        inf_feature = False
        if not len(np.unique(features)) == 8:
            # This feature extends infinitely
            inf_feature = True
        # Check each atom to determine how many atoms it surrounds
        surrounded_sites = []
        for i, site in enumerate(self.structure):
            # Get the voxel coords of each atom in their equivalent spots in each
            # quadrant of the supercell
            frac_coords = site.frac_coords
            transformed_coords = transformations + frac_coords
            voxel_coords = self.elf_grid.get_voxel_coords_from_frac_full_array(
                transformed_coords
            ).astype(int)
            # Get the feature label at each transformation. If the atom is not surrounded
            # by this basin, at least some of these feature labels will be the same
            features = inverted_feature_supercell[
                voxel_coords[:, 0], voxel_coords[:, 1], voxel_coords[:, 2]
            ]
            # print(len(np.unique(features)))
            if len(np.unique(features)) == 8:
                # The atom is completely surrounded by this basin and the basin belongs
                # to this atom
                surrounded_sites.append(i)
        surrounded_sites.extend(init_atoms)
        surrounded_sites = np.unique(surrounded_sites)
        if not inf_feature:
            return surrounded_sites
        else:
            if len(surrounded_sites) == 0:
                return surrounded_sites
            else:
                return np.insert(surrounded_sites, 0, -1)

    def get_bifurcation_graphs(
        self,
        resolution: float = 0.02,
        **cutoff_kwargs,
    ):
        """
        This will construct a bifurcation graph using a networkx
        DiGraph. Each node will contain information on whether it is
        reducible/irreducible, atomic/valent, etc. The resolution controls
        how big of a jump is made when scanning through the ELF.

        If the calculation is spin polarized, two graphs will be returned,
        one for each spin
        """
        if self.spin_polarized:
            elf_grid = self._elf_grid_up
            charge_grid = self._charge_grid_up
        else:
            elf_grid = self.elf_grid
            charge_grid = self.charge_grid
        # Get either the spin up graph or combined spin graph
        graph_up = self._get_bifurcation_graph(
            self.bader_up, elf_grid, charge_grid, resolution, **cutoff_kwargs
        )
        if self.spin_polarized:
            # Check if there's any difference in each spin. If not, we only need
            # to run this once. We set the tolerance such that all ELF values must
            # be within 0.0001 of each other
            if np.allclose(
                self._elf_grid_up.total, self._elf_grid_down.total, rtol=0, atol=1e-4
            ):
                logging.info("Spin grids are found to be equal. Using spin up only.")
                graph_down = graph_up.copy()
            else:
                # Get the spin down graph
                graph_down = self._get_bifurcation_graph(
                    self.bader_down,
                    self._elf_grid_down,
                    self._charge_grid_down,
                    resolution,
                    **cutoff_kwargs,
                )
            return graph_up, graph_down
        else:
            # We don't use spin polarized, so return the one graph.
            return graph_up

    def _get_bifurcation_graph(
        self,
        bader,
        elf_grid,
        charge_grid,
        resolution: float = 0.02,
        shell_depth: float = 0.05,
        metal_depth_cutoff: float = 0.1,
        min_covalent_angle: float = 150,
        min_covalent_bond_ratio: float = 0.35,
    ):
        """
        This will construct a BifurcationGraph class.
        Each node will contain information on whether it is
        reducible/irreducible, atomic/valent, etc. The resolution controls
        how big of a jump is made when scanning through the ELF.

        This method is largely meant to be called through the get_bifurcation_graphs
        method.
        """

        elf_data = elf_grid.total
        basin_labeled_voxels = bader.bader_volumes.copy()
        # create a graph with a base node to start tracking features
        graph = BifurcationGraph()
        graph.add_node(1, subset=1)
        # create an initial featured grid representing an ELF cutoff of 0
        featured_grid = np.ones(elf_grid.shape)
        # keep track of the total number of labels we've had throughout the
        # process. We use this to keep track of previous nodes
        total_features = 1

        for i in range(round(1 / resolution)):
            cutoff = resolution * (i + 1)
            cutoff_elf_grid = np.where(elf_data >= cutoff, 1, 0)
            # label our data to get the unique features
            label_structure = np.ones([3, 3, 3])
            # copy previous features
            old_featured_grid = featured_grid.copy()
            featured_grid, _ = label(cutoff_elf_grid, label_structure)
            # Check if we have the exact same array as before and if so, skip
            if np.array_equal(featured_grid, old_featured_grid):
                continue
            # Features connected through opposite sides of the unit cell should
            # have the same label, but they don't currently. To handle this, we
            # pad our featured grid, re-label it, and check if the new labels
            # contain multiple of our previous labels.
            featured_grid = self.wrap_labeled_grid(featured_grid)
            # We use values of 1 and up to assign nodes. We don't want to accidentally
            # overwrite these so we subtract the length of unique features to
            # make all of our values 0 and below
            unique_old_labels = np.unique(old_featured_grid)
            unique_new_labels = np.unique(featured_grid)
            old_len = len(unique_old_labels)
            new_len = len(unique_new_labels)
            featured_grid -= new_len
            unique_new_labels -= new_len
            # Prior to decreasing our values, 0 referred to areas with no feature.
            # We don't want to consider these regions so we remove them from
            # our unique lists
            if -old_len in unique_old_labels:
                unique_old_labels = unique_old_labels[1:]
            if -new_len in unique_new_labels:
                unique_new_labels = unique_new_labels[1:]

            if len(unique_old_labels) == 0:
                # we have no more features and are done so we break
                break

            # Now we want to loop over previous features and see which one(s)
            # split into multiple new features. As features split or dissapear
            # we label them with useful information
            for feature in unique_old_labels:
                mask = old_featured_grid == feature
                new_features = featured_grid[mask]
                features_list = np.unique(new_features)
                # get the node attributes corresponding to this old feature
                parent_idx = graph.parent_index(feature)
                parent = graph.parent_dict(feature)
                # remove 0
                if -new_len in features_list:
                    features_list = features_list[1:]
                if len(features_list) == 0:
                    # This feature was irreducible and just disappeared.
                    # We want to assign the feature to be atomic or valent and
                    # then store information that might be relavent to the type
                    # of basin it is.
                    # First we get easy information such as the max ELF and depth
                    # of the feature
                    max_elf = round(np.max(elf_data[mask]), 2)
                    split = parent["split"]
                    depth = round(max_elf - split, 2)
                    # Now we get the basins that belong to this feature.
                    # NOTE: there may be more than one if the depth of the basin is
                    # smaller than the resolution
                    # basins = np.unique(basin_labeled_voxels[mask])
                    basins = graph.nodes[feature]["basins"]
                    # Using these basins, we create a mask representing the full
                    # basin (not just above this elf value) and integrate the
                    # charge in this region. We also save the volume here
                    charge_mask = np.isin(basin_labeled_voxels, basins)
                    charge = round(
                        charge_grid.total[charge_mask].sum() / charge_grid.shape.prod(),
                        2,
                    )
                    volume = round(
                        len(np.where(charge_mask)[0]) * elf_grid.voxel_volume, 2
                    )
                    # We can also get the distance of this feature to the nearest
                    # atom and what that atom is. We have to assume we have several
                    # basins, so we use the shortest distance and corresponding ato
                    distances = bader.bader_distance[basins]
                    distance = distances.min()
                    nearest_atom = bader.bader_atoms[basins][
                        np.where(distances == distance)[0][0]
                    ]

                    # Now we update this node with the information we gathered
                    networkx.set_node_attributes(
                        graph,
                        {
                            feature: {
                                "max_elf": max_elf,
                                "depth": depth,
                                "charge": charge,
                                "volume": volume,
                                "atom_distance": distance,
                                "nearest_atom": nearest_atom,
                            }
                        },
                    )
                    # TODO: Add other important features? e.g. coordination env

                elif len(features_list) == 1:
                    # This typically means we have the same topological feature
                    # as before. There is occassionally a bug with the feature
                    # finder at low grid densities where a feature is found and
                    # then disapears in later rounds. In these cases, the incorrect
                    # feature will eventually include labels from other correct
                    # labels. (e.g. default Ti metal using vasp from matproj).
                    # From what I can tell, we should be able to remove those here
                    if features_list[0] > 0:
                        num = parent["num"] - 1
                        # atoms = parent["atoms"]
                        if num == 1:
                            # this node isn't useful anymore so we remove it
                            graph.remove_node(parent_idx)
                            # we also need to update the subset depth of all
                            # of our existing nodes
                            for node in graph.nodes:
                                graph.nodes[node]["subset"] -= 1
                        else:
                            # we've changed the number of children for this node
                            # so we update it
                            networkx.set_node_attributes(
                                graph, {parent_idx: {"num": num}}
                            )
                        # we don't want this node so we remove it
                        graph.remove_node(feature)
                    else:
                        # We have the same topological feature as before. Replace the
                        # feature label with the previous one
                        featured_grid = np.where(
                            featured_grid == features_list[0], feature, featured_grid
                        )
                elif len(features_list) > 1:
                    # This feature has split and we want to add an attribute
                    # labeling it with the value it split at. We also want to
                    # record how many features it split into, the basins that
                    # are in this feature, and if there are any atoms contained
                    # in it. This info may be used later to categorize basin.
                    # basins = np.unique(basin_labeled_voxels[mask])
                    # Our current mask is the last point where this feature was
                    # distinct, but we want the point where it had the lowest
                    # ELF value while being distinct. This allows us to see if
                    # this feature fully surrounded an atom.
                    if parent is not None:
                        parent_split = parent.get("split", None)
                        basins = graph.nodes[feature]["basins"]
                        low_elf_mask = np.isin(basin_labeled_voxels, basins) & np.where(
                            elf_grid.total > parent_split, True, False
                        )
                        atoms = self.get_atoms_surrounded_by_volume(low_elf_mask)
                    else:
                        # if we have no parent this is our first node and
                        # we have as many atoms as there are in the structure
                        atoms = [i for i in range(len(self.structure))]
                        # This is always infinite, so we note that by adding -1
                        # to the front of our list
                        atoms.insert(0, -1)
                    # If the volume surrounds infinite atoms, the first atom
                    # returned will be a -1. We check for this
                    if len(atoms) > 0:
                        if atoms[0] == -1:
                            atom_num = -1
                            atoms = atoms[1:]
                        else:
                            atom_num = len(atoms)
                    networkx.set_node_attributes(
                        graph,
                        {
                            feature: {
                                "split": cutoff,
                                "num": len(features_list),
                                "atoms": atoms,
                                "atom_num": atom_num,
                            }
                        },
                    )
                    # We have new features and we want to label them as such
                    for new_feat in features_list:
                        total_features += 1
                        # relabel feature
                        featured_grid = np.where(
                            featured_grid == new_feat, total_features, featured_grid
                        )
                        # Add node to our graph
                        graph.add_node(total_features)
                        graph.add_edge(feature, total_features)
                        # add an attribute for the depth of this feature as well
                        # as the basins that belong to this feature
                        feature_mask = featured_grid == total_features
                        basins = np.unique(basin_labeled_voxels[feature_mask])
                        depth = len(networkx.ancestors(graph, total_features)) + 1
                        networkx.set_node_attributes(
                            graph,
                            {
                                total_features: {
                                    "subset": depth,
                                    "basins": basins,
                                }
                            },
                        )
        # Now we have a graph with information associated with each basin. We want
        # to label each node.
        graph = self._mark_atomic(graph, bader, elf_grid, shell_depth)
        # In some cases, the user may not have used a pseudopotential with enough core electrons.
        # This can result in an atom having no assigned core/shell, which will
        # result in nonsense later. We check for this here and throw an error
        assigned_atoms = []
        for i in graph.nodes:
            node = graph.nodes[i]
            # We only want to consider basins that are core or shell, so we check
            # here and skip otherwise
            basin_subtype = node.get("subtype", None)
            if not basin_subtype in ["core", "shell"]:
                continue
            atom = node.get("nearest_atom", None)
            if atom is not None:
                assigned_atoms.append(atom)
        if (
            len(np.unique(assigned_atoms)) != len(self.structure)
            and not self.ignore_low_pseudopotentials
        ):
            # BUG: This exception was flagged for SiO despite there being atom assignments for the full structure
            raise Exception(
                "At least one atom was not assigned a zero-flux basin. This typically results"
                "from pseudo-potentials (PPs) with only valence electrons (e.g. the defaults for Al, Si, B in VASP 5.X.X)."
                "Try using PPs with more valence electrons such as VASP's GW potentials"
            )

        # Now we want to label our valence features as Covalent, Metallic, or bare electron.
        # Many covalent and metallic features are easy to find. Covalent bonds
        # are typically exactly along a bond between an atom and its nearest
        # neighbors. Metallic features have a low depth. We mark these first
        graph = self._mark_metallic_covalent(
            bader,
            graph,
            metal_depth_cutoff=metal_depth_cutoff,
            min_covalent_angle=min_covalent_angle,
            min_covalent_bond_ratio=min_covalent_bond_ratio,
        )

        # Now we calculate a bare electron indicator for each valence basin. This
        # is used just to give a sense of how bare an electron is.
        graph = self._mark_bare_electron_indicator(graph, bader, elf_grid)

        # Finally, we add a label to each node with a summary of information
        # for plotting
        for i in graph.nodes:
            node = graph.nodes[i]
            if "split" in node.keys():
                networkx.set_node_attributes(
                    graph,
                    {
                        i: {
                            "label": f"split: {node['split']}\n num: {node['num']}\n atom_num: {node['atom_num']}",
                        }
                    },
                )

            else:
                try:
                    networkx.set_node_attributes(
                        graph,
                        {
                            i: {
                                "label": f"max: {node['max_elf']}\ndepth: {node['depth']}\n charge: {node['charge']}\n type: {node['subtype'] or node['type']}\n",
                            }
                        },
                    )
                except:
                    raise Exception(
                        "At least one feature was not assigned. This is a bug. Please report to our github:"
                        "https://github.com/jacksund/simmate/issues"
                    )

        return graph

    def get_valence_summary(self, graph: BifurcationGraph()) -> dict:
        """
        Takes in a bifurcation graph and summarizes any valence basin
        information as a nested dictionary where each key is the node
        index and each value is a dictionary of useful information
        """
        summary = {}
        for i in graph.nodes:
            node = graph.nodes[i]
            basin_type = node.get("type", None)
            if basin_type == "val":
                summary[i] = node
        return summary

    def _mark_atomic(
        self,
        graph: BifurcationGraph(),
        bader,
        elf_grid,
        shell_depth: float = 0.05,
    ):
        elf_data = elf_grid.total
        basin_labeled_voxels = bader.bader_volumes.copy()
        # create a variable to track the number of atoms left to assign
        remaining_atoms = len(self.structure)
        # BUG: The remaining atom count is broken currently. Sometimes atoms are
        # double counted, e.g. when a core feature breaks off before another feature
        # that fully surround the atom.
        for i in graph.nodes:
            # Get the dict of information for our node and the parent of our node
            node = graph.nodes[i]
            # We are going to use attributes of each irreducible feature to
            # assign its children, so if this node isn't irreducible we skip it
            if not "split" in node.keys():
                continue
            # We also label this node with how many atoms are left to assign
            networkx.set_node_attributes(
                graph, {i: {"remaining_atoms": remaining_atoms}}
            )
            # There are three situations for our reducible feature. First, if
            # it surrounds 0 atoms then all of its children must be valence. We
            # skip in this case
            num_atoms = node["atom_num"]
            if num_atoms == 0:  # or remaining_atoms == 0:
                # Label all children as valence
                for child_idx, child in graph.child_dicts(i).items():
                    # skip an reducible features
                    if "split" in child.keys():
                        continue
                    # We sometimes label the nodes of reducible features as covalent.
                    # We don't want to overwrite these so we check that the subtype
                    # doesn't exist
                    elif child.get("subtype") is None:
                        networkx.set_node_attributes(
                            graph, {child_idx: {"type": "val", "subtype": None}}
                        )
                continue
            # Second, it can contain more than one atom. In a full core model,
            # The atoms that split off of this type of feature would themselves
            # be reducible and always fit into the next category. However, with
            # a pseudopotential model, this is not the case. Instead, an atom
            # may only have a single irreducible feature. We check for this by
            # noting if the child features fully surround an atom at the ELF they separate at
            # NOTE: -1 atoms really indicates infinite
            # TODO: It may be that this loop should just be for when the number
            # of atoms is infinite. Basically, any finite number suggests a
            # molecular feature and all basins would be core/shell/covalent/lone-pair.
            # elif num_atoms > 1 or num_atoms == -1:# and remaining_atoms > 0:
            elif num_atoms == -1:
                for child_idx, child in graph.child_dicts(i).items():
                    # skip any nodes that are reducible
                    if "split" in child.keys():
                        continue
                    # Get the basins that belong to this child
                    basins = child["basins"]
                    # Using these basins, and the value the basin split at, we
                    # get a mask for the location of the basin
                    parent_split = node["split"]
                    low_elf_mask = np.isin(basin_labeled_voxels, basins) & np.where(
                        elf_data > parent_split, True, False
                    )
                    atoms_in_basin = self.get_atoms_surrounded_by_volume(low_elf_mask)
                    # TODO: We can probably check if these basins are cores or a shell around the atom
                    basin_type = "val"
                    basin_subtype = None
                    if len(atoms_in_basin) > 0:
                        basin_type = "atom"
                        basin_subtype = "core"
                        # Note that we found a new atom
                        remaining_atoms -= 1
                    # label this basin
                    networkx.set_node_attributes(
                        graph,
                        {child_idx: {"type": basin_type, "subtype": basin_subtype}},
                    )
            # The final option is that our reducible region surrounds a finite
            # number of atoms. Most of the subregions of this
            # environment will be atomic, but they can be of several types including
            # atom shells/cores, unshared electrons, lone-pairs. The one exception
            # is heterogenous covalent bonds, which should be shared.
            # elif num_atoms == 1:
            elif num_atoms > 0:
                # first we check that this reducible region isn't itself a child
                # of a reducible region with 1 atom. If it's not we note that
                # we've found an atom
                parent = graph.parent_dict(i)
                if "split" in parent.keys():
                    if not parent["atom_num"] == 1:
                        remaining_atoms -= 1
                # Now we loop over all of the children of this feature, including
                # deeper children. We label these children based on their depth
                # and whether they surround the atom. We label features as:
                # core, shell, or other.
                # The "others" will be assigned later on as lone-pairs or covalent
                # depending on if they are along an atomic bond
                for child_idx, child in graph.deep_child_dicts(i).items():
                    # define our default types
                    basin_type = "atom"
                    basin_subtype = None
                    # If we have a split, we don't want to label this node so
                    # we continue.
                    if "split" in child.keys():
                        continue
                    # If we have many shell basins that form a sphere around the
                    # atom they may separate at a low depth. To account for this
                    # we assign any low depth features as shells
                    if child["depth"] < shell_depth:
                        basin_subtype = "shell"
                    else:
                        # otherwise, we check if the feature surrounds an atom
                        # Get the basins that belong to this child
                        basins = child["basins"]
                        # Using these basins, and the value the basin split at, we
                        # get a mask for the location of the basin
                        parent_split = node["split"]
                        low_elf_mask = np.isin(basin_labeled_voxels, basins) & np.where(
                            elf_data > parent_split, True, False
                        )
                        atoms_in_basin = self.get_atoms_surrounded_by_volume(
                            low_elf_mask
                        )
                        if len(atoms_in_basin) > 0:
                            # We have an core/shell region
                            basin_subtype = "core"
                        else:
                            # otherwise its an other
                            basin_type = "val"
                            basin_subtype = "other"
                    # Now we assign our types to the child node.
                    networkx.set_node_attributes(
                        graph,
                        {child_idx: {"type": basin_type, "subtype": basin_subtype}},
                    )
        # Reduce any related shell basins to a single basin
        graph = self._reduce_atomic_shells(graph)

        return graph

    def _reduce_atomic_shells(
        self,
        graph: BifurcationGraph(),
    ) -> BifurcationGraph():
        """
        Reduces shell nodes to a single node
        """
        children_to_remove = []
        for i in graph.nodes:
            new_children_to_remove = []
            # We should now have assigned all of our core and shell basins. For
            # convenient visualization we want to combine all of our shell basins
            # into one node.
            basins = []
            atom_distance = 50
            volume = 0
            charge = 0
            max_elf = 0
            nearest_atom = 0
            subset = 0

            all_shells = True
            # update all of our shell characteristics
            for child_idx, child in graph.child_dicts(i).items():
                if not child.get("subtype", None) == "shell":
                    all_shells = False
                    continue
                new_children_to_remove.append(child_idx)
                basins.extend(child["basins"])
                atom_distance = min(atom_distance, child["atom_distance"])
                volume += child["volume"]
                charge += child["charge"]
                max_elf = max(max_elf, child["max_elf"])
                nearest_atom = child["nearest_atom"]
                subset = child["subset"]
            if len(new_children_to_remove) == 0:
                # we had no shells so we can just continue
                continue
            if all_shells:
                # This shell only had other shells as siblings. This means our
                # parent node should be replaced with our new shell information
                # and our depth should be calculated by our parent's parent
                node_to_replace = i
                parent = graph.parent_dict(i)
                parent_elf = parent["split"]
                depth = max_elf - parent_elf
                subset -= 1
            else:
                # we had some features other than shells. We want to replace the
                # first shell node
                node_to_replace = new_children_to_remove.pop(0)
                depth = max_elf - graph.nodes[i]["split"]

            # clear the attributes from the node
            graph.nodes[node_to_replace].clear()
            # Add the attributes
            networkx.set_node_attributes(
                graph,
                {
                    node_to_replace: {
                        "type": "atom",
                        "subtype": "shell",
                        "subset": subset,
                        "atom_distance": round(atom_distance, 2),
                        "volume": round(volume, 2),
                        "charge": round(charge, 2),
                        "max_elf": round(max_elf, 2),
                        "nearest_atom": nearest_atom,
                        "depth": round(depth, 2),
                    }
                },
            )
            children_to_remove.extend(new_children_to_remove)
        # delete all of the unused nodes
        for j in children_to_remove:
            graph.remove_node(j)

        return graph

    def _mark_metallic_covalent(
        self,
        bader,
        graph: BifurcationGraph(),
        metal_depth_cutoff: float = 0.1,
        min_covalent_angle: float = 135,
        min_covalent_bond_ratio: float = 0.35,
    ) -> BifurcationGraph():
        """
        Takes in a bifurcation graph and labels valence features that
        are obviously metallic or covalent
        """
        valence_summary = self.get_valence_summary(graph)
        # TODO: Many of these features could be symmetric. I should only perform
        # each action for one of these symmetric features and assign the result
        # to all of them.
        for feature_idx, attributes in valence_summary.items():
            previous_subtype = attributes.get("subtype")
            # Default to bare electron
            basin_type = "val"
            subtype = "bare electron"
            # first check for metallic character as this is easy. Note we make
            # sure this feature isn't already assigned as covalent to avoid relabeling
            # features that have already been found
            if attributes["depth"] < metal_depth_cutoff and previous_subtype != "other":
                subtype = "metallic"
                # set subtype
                networkx.set_node_attributes(graph, {feature_idx: {"subtype": subtype}})
                continue
            # next check for covalent character
            # We create a temporary structure to calculate distances to neighboring
            # atoms. This is just to utilize pymatgen's distance method which
            # takes periodic boundaries into account.
            # TODO: This may be slow for larger structures. This could probably
            # be done using numpy arrays and the structure.distance_matrix
            # We assume there is only one basin, as this is the typical case for
            # covalent bonds
            frac_coords = bader.bader_maxima_fractional[attributes["basins"][0]]
            temp_structure = self.structure.copy()
            temp_structure.append("X", frac_coords)
            nearest_atom = attributes["nearest_atom"]
            atom_dist = round(temp_structure.get_distance(nearest_atom, -1), 2)
            atom_neighs = self.atom_coordination_envs[nearest_atom]
            # We want to see if our feature lies directly between our atom and
            # any of its neighbors.
            covalent = False
            for neigh_dict in atom_neighs:
                # We use the temp structure to calculate distance between the
                # feature and neighbors. This automatically acounts for wrapping
                # in the unit cell
                neigh_idx = neigh_dict["site_index"]
                neigh_dist = round(temp_structure.get_distance(neigh_idx, -1), 2)
                # We use the distance calculated by cnn for the atom/neigh dist
                atom_neigh_dist = round(neigh_dict["site"].nn_distance, 2)
                # Sometimes we have a lone-pair that appears to be within our
                # angle cutoff (e.g. CaC2), but is much closer to one atom than
                # a covalent bond would be. We check for this here with a ratio.
                atom_dist_ratio = atom_dist / atom_neigh_dist
                if atom_dist_ratio < min_covalent_bond_ratio:
                    continue
                # We want to apply the law of cosines to get angle with feature
                # at center, then convert to degrees. This won't work if our feature
                # is exactly along the bond, so we first check for that case.
                test_dist = round(atom_dist + neigh_dist, 2)
                if test_dist == atom_neigh_dist:
                    covalent = True
                    break
                try:
                    feature_angle = math.acos(
                        (atom_dist**2 + neigh_dist**2 - atom_neigh_dist**2)
                        / (2 * atom_dist * neigh_dist)
                    )
                    feature_angle = feature_angle * 180 / math.pi
                except:
                    # We don't have a valid triange. This can happen if the feature
                    # is along the bond but not between the atoms (lone-pairs)
                    # or if we are comparing atoms not near the lone pair. In
                    # either case we don't have a covalent bond and continue
                    continue

                # check that we're above the cutoff
                if feature_angle > min_covalent_angle:
                    covalent = True
                    break
            # Now we've noted if our feature is covalent. If it is, we label it
            # as such
            if covalent:
                subtype = "covalent"
            # We also noted in our atomic assignment which features were part
            # of the atomic branch, but weren't shells or cores. The remaining
            # options were covalent or lone-pairs and we've just assigned the
            # covalent ones. So, if our previous subtype was "other" and the
            # feature isn't covalent it must be a lone-pair
            if previous_subtype == "other" and not covalent:
                subtype = "lone-pair"

            # We've now checked for metallic character, covalent bonds and most
            # lone-pairs. We update our subtype accordingly
            networkx.set_node_attributes(
                graph, {feature_idx: {"type": basin_type, "subtype": subtype}}
            )
        # There is an exception to the lone-pair rule that can result in missing
        # a lone-pair assignment. If a covalent/lone-pair feature surrounds two atoms
        # these features won't be assigned as "other".
        # This happens in CaC2 around the C2 molecules for example. The covalent
        # bonds are labeled in the loop above, but the lone-pair will
        # still be labeled as a bare electron. We correct for this in an
        # additional loop by checking for bare electrons that are siblings with
        # covalent bonds.
        features_to_relabel = []
        for feature_idx, attributes in valence_summary.items():
            if attributes.get("subtype") == "bare electron":
                # Check if all siblings are covalent, bare electrons, or lone-pairs. If so,
                # this is a lone-pair
                all_cov_lp_be = True
                at_least_one_cov = False
                for sibling_idx, sibling in graph.sibling_dicts(feature_idx).items():
                    if "split" in sibling.keys():
                        continue
                    # We need to make sure there's at least one covalent bond as well
                    if sibling["subtype"] == "covalent":
                        at_least_one_cov = True
                    elif sibling["subtype"] not in [
                        "bare electron",
                        "covalent",
                        "lone-pair",
                    ]:
                        all_cov_lp_be = False
                if all_cov_lp_be and at_least_one_cov:
                    features_to_relabel.append(feature_idx)
        for feature_idx in features_to_relabel:
            networkx.set_node_attributes(
                graph, {feature_idx: {"type": "val", "subtype": "lone-pair"}}
            )

        return graph

    def _mark_bare_electron_indicator(
        self, graph: BifurcationGraph(), bader, elf_grid: Grid,
    ) -> BifurcationGraph():
        """
        Takes in a bifurcation graph and calculates an electride character
        score for each unlabeled valence feature. Electride character ranges from
        0 to 1 and is the combination of several different metrics:
        ELF value, charge, depth, volume, and atom distance.
        """
        valence_summary = self.get_valence_summary(graph)
        # We will need to get radii from the ELF. To do this, we need a labeled
        # pybader result to pass to our PartitioningToolkit
        frac_coords = bader.bader_maxima_fractional
        temp_structure = self.structure.copy()
        for feature_idx, attributes in valence_summary.items():
            for basin_idx in attributes["basins"]:
                frac_coord = frac_coords[basin_idx]
                temp_structure.append("X", frac_coord)
        temp_grid = elf_grid.copy()
        temp_grid.structure = temp_structure
        #TODO This can probably be made faster by rerunning only part of the
        # bader. If not this should be passed to the BadELfToolkit to avoid
        # repeat calculation. Also, I need to account for threads. Also, update radius finder
        # to only use linear interpolation. Update finder to get all atom radii
        # once.
        labeled_pybader = temp_grid.run_pybader()
        partitioning = PartitioningToolkit(elf_grid, labeled_pybader)
        
        
        for feature_idx, attributes in valence_summary.items():
            # We want to get a metric of how "bare" each feature is. To do this,
            # we need a value that ranges from 0 to 1 for each attribute we have
            # available. We can combine these later with or without weighting to
            # get a final value from 0 to 1.
            # First, the ELF value already ranges from 0 to 1, with 1 being more
            # localized. We don't need to alter this in any way.
            elf_contribution = attributes["max_elf"]

            # next, we look at the charge. If we are using a spin polarized result
            # the maximum amount should be 1. Otherwise, the value could be up
            # to 2. We make a guess at what the value should be here
            charge = attributes["charge"]
            if self.spin_polarized:
                max_value = 1
            else:
                if 0 < charge <= 1.1:
                    max_value = 1
                else:
                    max_value = 2
            # Anything significantly below our indicates metallic character and
            # anything above indicates a feature like a covalent bond with pi contribution.
            # we use a symmetric linear equation around our max value that maxes out at 1
            # where the charge exactly matches and decreases moving away.
            if charge <= max_value:
                charge_contribution = charge / max_value
            else:
                # If somehow our charge is much greater than the value, we will
                # get a negative value, so we use a max function to prevent this
                charge_contribution = max(-charge / max_value + 2, 0)

            # Now we look at the depth of our feature. Like the ELF value, this
            # can only be from 0 to 1, and bare electrons tend to take on higher
            # values. Therefore, we leave this as is
            depth_contribution = attributes["depth"]

            # Next is the volume. Bare electrons are usually thought of as being
            # similar to a free s-orbital with a similar size to a hydride. Therefore
            # we use the hydride crystal radius to calculate an ideal volume and set
            # this contribution as a fraction of this, capping at 1.
            hydride_radius = 1.34  # Taken from wikipedia and subject to change
            hydride_volume = 4 / 3 * 3.14159 * (hydride_radius**3)
            volume_contribution = min(attributes["volume"] / hydride_volume, 1)

            # Next is the distance from the atom. Ideally this should be scaled
            # relative to the radius of the atom, but which radius to use is a
            # difficult question. We use CrystalNN to get the neighbors around
            # the nearest atom and get the EN difference. We use this to guess
            # whether covalent or ionic radii should be used, then pull the appropriate one.
            atom_idx = attributes["nearest_atom"]
            # atom_radius = self.get_atom_radius_guess(atom_idx)
            atom_radius = partitioning.get_elf_ionic_radius(atom_idx, refine=False)
            dist = attributes["atom_distance"]
            # Now that we have a radius, we need to get a metric of 0-1. We need
            # to set an ideal distance corresponding to 1 and a minimum distance
            # corresponding to 0. The ideal distance is the sum of the atoms radius
            # plus the radius of a true bare electron (approx the H- radius). The
            # minimum distance is somewhat arbitrary, but should be around the
            # atoms radius as this corresponds to covalent bond type behavior.
            # We set the minimum to 90% of the atoms radius to account for variation
            min_dist = atom_radius * 0.9
            max_dist = atom_radius + hydride_radius
            dist_contribution = (dist - min_dist) / (max_dist - min_dist)
            # limit to a range of 0 to 1
            dist_contribution = min(max(dist_contribution, 0), 1)
            dist_minus_radius = dist - atom_radius

            # Finally, our bare electron indicator is a linear combination of
            # the indicator above. The contributions are somewhat arbitrary, but
            # are based on chemical intuition. The ELF and charge contributions
            contributers = np.array(
                [
                    elf_contribution,
                    charge_contribution,
                    depth_contribution,
                    volume_contribution,
                    dist_contribution,
                ]
            )
            weights = np.array(
                [
                    0.2,
                    0.2,
                    0.2,
                    0.2,
                    0.2,
                ]
            )
            bare_electron_indicator = np.sum(contributers * weights)
            # we update our node to include this information
            networkx.set_node_attributes(
                graph,
                {
                    feature_idx: {
                        "bare_electron_indicator": bare_electron_indicator,
                        "bare_electron_scores": contributers,
                        "dist_minus_radius": dist_minus_radius,
                    }
                },
            )
        return graph

    def get_bifurcation_plots(
        self,
        resolution: float = 0.02,
        write_plot: bool = False,
        plot_name="bifurcation_plot.html",
        **cutoff_kwargs,
    ):
        """
        Plots bifurcation plots automatically. Graphs will be generated
        using the provided resolution. If the provided
        ELF and Charge Density are spin polarized, two plots will be
        generated.
        """
        # remove .html if its at the end of the plot name
        plot_name = plot_name.replace(".html", "")

        if self.spin_polarized:
            graph_up, graph_down = self.get_bifurcation_graphs(
                resolution,
                **cutoff_kwargs,
            )
            plot_up = self.get_bifurcation_plot(
                graph_up, write_plot, f"{plot_name}_up.html"
            )
            plot_down = self.get_bifurcation_plot(
                graph_down, write_plot, f"{plot_name}_down.html"
            )
            return plot_up, plot_down
        else:
            graph = self.get_bifurcation_graphs(resolution, **cutoff_kwargs)
            return self.get_bifurcation_plot(graph, write_plot, plot_name)

    def get_bifurcation_plot(
        self,
        graph: BifurcationGraph(),
        write_plot=False,
        plot_name="bifurcation_plot.html",
    ):
        """
        Returns a plotly figure
        """
        # remove .html if its at the end of the plot name
        plot_name = plot_name.replace(".html", "")
        # then add .html to ensure its there
        plot_name += ".html"

        indices = []
        end_indices = []
        # X position is determined by the ELF value at which the feature appears.
        Xn = []
        labels = []
        types = []
        for i in graph.nodes():
            indices.append(i)
            node = graph.nodes[i]
            if node.get("split", None) is None:
                end_indices.append(i)
                # Get label
                label = f"""type: {node["subtype"]}\ndepth: {node["depth"]}\nmax elf: {node["max_elf"]}\ncharge: {node["charge"]}\nvolume: {node["volume"]}\natom distance: {round(node["atom_distance"],2)}\nnearest atom index: {node["nearest_atom"]}\nnearest atom type: {self.structure[node["nearest_atom"]].specie.name}"""
                if node.get("bare_electron_indicator", None) is not None:
                    label += f'\ndistance minus atom radius: {round(node["dist_minus_radius"],2)}'
                #     label += f"\nBEI array: {node['bare_electron_scores'].round(2)}"
                types.append(node["subtype"])
            else:
                atom_num = node["atom_num"]
                if atom_num == -1:
                    atom_num = "infinite"
                label = f"""type: reducible\ncontained atoms: {node["atoms"]}\ntotal contained atoms: {atom_num}"""
                types.append("reducible")
            # change to html line break
            label = label.replace("\n", "<br>")
            labels.append(label)
            parent = graph.parent_dict(i)
            if parent is not None:
                Xn.append(parent["split"])
            else:
                Xn.append(0)
        # Now we get the Y positions. First, we calculate how spread out each end node should
        # be.
        max_y = 2
        y_division = max_y / len(end_indices)
        # create a list for storing the Y values. Set each value to 0 for now
        Yn = [0 for i in range(len(Xn))]
        # Now we set the values for each end node by spreading them evenly.
        for index_n, index in enumerate(end_indices):
            Yn[indices.index(index)] = index_n * y_division
        # Now we get the y locations for each split node. We do this in reverse because
        # some split nodes may be parents of later split nodes and we want to make sure
        # all children have an assigned y
        reverse_indices = indices.copy()
        reverse_indices.reverse()
        for i in reverse_indices:
            node = graph.nodes[i]
            # check that this is a split node
            if node.get("split", None) is not None:
                # for each child, grab it's current y value
                children = graph.child_indices(i)
                child_ys = [Yn[indices.index(child_idx)] for child_idx in children]
                # take the average and assign this as our new y value
                y = np.average(child_ys)
                Yn[indices.index(i)] = y

        # Now we need to get the lines that will be used for each edge. These will use
        # a nested lists where each edge has one entry and the sub-lists contain the
        # two x and y entries for each edge.
        Xe = []
        Ye = []
        for edge in graph.edges():
            parent = edge[0]
            child = edge[1]
            Xe.extend([Xn[indices.index(parent)], Xn[indices.index(child)], None])
            Ye.extend([Yn[indices.index(parent)], Yn[indices.index(child)], None])

        # create the figure and add the lines and nodes
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=Xe,
                y=Ye,
                mode="lines",
                name="connection",
                line=dict(color="rgb(210,210,210)", width=1),
                hoverinfo="none",
            )
        )

        # convert lists to numpy arrays for easy querying
        types = np.array(types)
        labels = np.array(labels)
        Xn = np.array(Xn)
        Yn = np.array(Yn)
        # add nodes for each type of point
        for basin_type in np.unique(types):
            # Color code by type
            if basin_type == "reducible":
                color = "#808080"  # grey
            elif basin_type == "shell" or basin_type == "core":
                color = "#000000"  # black
            elif basin_type == "covalent":
                color = "#00FFFF"  # aqua
            elif basin_type == "metallic":
                color = "#C0C0C0"  # silver
            elif basin_type == "lone-pair":
                color = "#800080"  # purple
            elif basin_type == "bare electron":
                color = "#800000"  # maroon

            xs = Xn[np.where(types == basin_type)[0]]
            ys = Yn[np.where(types == basin_type)[0]]
            sub_labels = labels[np.where(types == basin_type)[0]]
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers",
                    name=f"{basin_type}",
                    marker=dict(
                        symbol="circle-dot",
                        size=36,
                        color=color,  #'#DB4551',
                        line=dict(color="rgb(50,50,50)", width=1),
                    ),
                    text=sub_labels,
                    hoverinfo="text",
                    opacity=0.8,
                )
            )

        # remove y axis label
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="ELF",
            yaxis=dict(
                showline=False,
                zeroline=False,
                showgrid=False,
                showticklabels=False,
            ),
        )

        if write_plot:
            fig.write_html(self.directory / plot_name)
        return fig

    def get_labeled_structures(
        self,
        resolution: float = 0.02,
        include_lone_pairs: bool = False,
        include_shared_features: bool = True,
        metal_depth_cutoff: float = 0.1,
        min_covalent_angle: float = 135,
        min_covalent_bond_ratio: float = 0.35,
        shell_depth: float = 0.05,
        electride_elf_min: float = 0.5,
        electride_depth_min: float = 0.2,
        electride_charge_min: float = 0.5,
        electride_volume_min: float = 10,
        electride_radius_min: float = 0.3,
    ):
        """
        Returns a structure with dummy atoms at electride and shared
        electron sites. Off atom basins are assigned using the bifurcation
        graph method. See the .get_bifurcation_plot method for more info.

        Dummy atoms will have the following labels:
        e: electride, le: bare electron, m: metallic feature, z: covalent bond,
        lp: lone-pair

        If spin porized files are provided, returns two structures.
        """
        if self.spin_polarized:
            graph_up, graph_down = self.get_bifurcation_graphs(
                resolution,
                shell_depth=shell_depth,
                metal_depth_cutoff=metal_depth_cutoff,
                min_covalent_angle=min_covalent_angle,
                min_covalent_bond_ratio=min_covalent_bond_ratio,
            )
            structure_up = self._get_labeled_structure(
                graph_up,
                self.bader_up,
                include_lone_pairs,
                include_shared_features,
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            )
            structure_down = self._get_labeled_structure(
                graph_down,
                self.bader_down,
                include_lone_pairs,
                include_shared_features,
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            )
            return structure_up, structure_down
        else:
            graph = self.get_bifurcation_graphs(
                resolution,
                shell_depth=shell_depth,
                metal_depth_cutoff=metal_depth_cutoff,
                min_covalent_angle=min_covalent_angle,
                min_covalent_bond_ratio=min_covalent_bond_ratio,
            )
            return self._get_labeled_structure(
                graph,
                self.bader_up,
                include_lone_pairs,
                include_shared_features,
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            )

    def _get_labeled_structure(
        self,
        graph: BifurcationGraph(),
        bader,
        include_lone_pairs: bool = False,
        include_shared_features: bool = True,
        electride_elf_min: float = 0.5,
        electride_depth_min: float = 0.2,
        electride_charge_min: float = 0.5,
        electride_volume_min: float = 10,
        electride_radius_min: float = 0.3,
    ):
        # First, we get the valence features for this graph and create a
        # structure that we will add features to
        valence_features = self.get_valence_summary(graph)
        structure = self.structure.copy()
        structure.remove_oxidation_states()
        empty_structure = structure.copy()
        empty_structure.remove_species(empty_structure.symbol_set)
        # create an array of our conditions to check against
        conditions = np.array(
            [
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            ]
        )
        for feat_idx, attributes in valence_features.items():
            # get our subtype
            subtype = attributes["subtype"]
            # if our subtype is anothing other than "bare electron" we have
            # a covalent bond or metal bond and append a Z dummy atom
            if subtype == "covalent":
                if not include_shared_features:
                    continue
                species = "z"
            elif subtype == "metallic":
                if not include_shared_features:
                    continue
                species = "m"
            elif subtype == "lone-pair":
                if not include_lone_pairs:
                    continue
                species = "lp"

            else:
                # we have a bare electron. We check each condition
                condition_test = np.array(
                    [
                        attributes["max_elf"],
                        attributes["depth"],
                        attributes["charge"],
                        attributes["volume"],
                        attributes["dist_minus_radius"],
                    ]
                )
                # check if we meet all conditions
                if np.all(condition_test > conditions):
                    species = "e"
                else:
                    if not include_shared_features:
                        continue
                    species = "le"

            # Now that we have the type of feature, we want to combine all
            # of its basins to a single point.
            basins = attributes["basins"]
            # Then we get their fractional coords
            frac_coords = bader.bader_maxima_fractional[basins]
            if len(frac_coords) == 1:
                structure.append(species, frac_coords[0])
            else:
                # We append these to an empty structure and use pymatgen's
                # merge method to get their average position
                temp_structure = empty_structure.copy()
                for frac_coord in frac_coords:
                    temp_structure.append("He", frac_coord)
                if len(temp_structure) > 1:
                    temp_structure.merge_sites(tol=1, mode="average")
                frac_coord = temp_structure.frac_coords[0]
                structure.append(species, frac_coord)

        # To find the atoms/electrides surrounding a covalent/metallic bond,
        # we need the structure to be organized with atoms first, then electrides,
        # then whatever else. We organize everything here.
        electride_indices = structure.indices_from_symbol("E")
        other_indices = []
        for symbol in ["M", "Le", "Z", "Lp"]:
            other_indices.extend(structure.indices_from_symbol(symbol))
        sorted_structure = self.structure.copy()
        sorted_structure.remove_oxidation_states()
        for i in electride_indices:
            frac_coords = structure[i].frac_coords
            sorted_structure.append("E", frac_coords)
        for i in other_indices:
            symbol = structure.species[i].symbol
            frac_coords = structure[i].frac_coords
            sorted_structure.append(symbol, frac_coords)

        logging.info(f"{len(electride_indices)} electride sites found")
        if len(other_indices) > 0:
            f"{len(other_indices)} shared sites found"

        return sorted_structure

    @classmethod
    def from_files(
        cls,
        directory: Path = Path("."),
        elf_file: str = "ELFCAR",
        charge_file: str = "CHGCAR",
        separate_spin: bool = False,
        ignore_low_pseudopotentials: bool = False,
    ):
        """
        Creates a BadElfToolkit instance from the requested partitioning file
        and charge file.

        Args:
            directory (Path):
                The path to the directory that the badelf analysis
                will be located in.
            elf_file (str):
                The filename of the file containing the ELF. Must be a VASP
                ELFCAR type file.
            charge_file (str):
                The filename of the file containing the charge information. Must
                be a VASP CHGCAR file.
            separate_spin (bool):
                Whether to check for spin and provider results for both. If this
                is False, only the first set of data in the provided files is
                used.

        Returns:
            A ElfAnalyzerToolkit instance.
        """

        elf_grid = Grid.from_file(directory / elf_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return ElfAnalyzerToolkit(
            elf_grid=elf_grid,
            charge_grid=charge_grid,
            directory=directory,
            separate_spin=separate_spin,
            ignore_low_pseudopotentials=ignore_low_pseudopotentials,
        )
