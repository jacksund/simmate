#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import math
import warnings
from functools import cached_property
from pathlib import Path

import matplotlib.pyplot as plt
import networkx
import numpy as np
import psutil
from networkx import DiGraph
from networkx.utils import UnionFind
from numpy.typing import NDArray
from pymatgen.analysis.local_env import CrystalNN
from scipy.ndimage import label

from simmate.apps.bader.toolkit import Grid
from simmate.toolkit import Structure


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


class ElectrideFinder:
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
        allow_spin: bool = False,
        ignore_low_pseudopotentials: bool = False,
    ):
        self.elf_grid = elf_grid.copy()
        self.charge_grid = charge_grid.copy()
        self.directory = directory
        self.ignore_low_pseudopotentials = ignore_low_pseudopotentials
        self._basin_labeled_voxels = None
        # check if this is a spin polarized calculation and if the user wants
        # to pay attention to this.
        if elf_grid.is_spin_polarized and allow_spin:
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
        graph = self.mark_atomic_basins(graph, bader, elf_grid, shell_depth)
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
            raise Exception(
                "At least one atom was not assigned a zero-flux basin. This typically results"
                "from pseudo-potentials (PPs) with only valence electrons (e.g. the defaults for Al, Si, B in VASP 5.X.X)."
                "Try using PPs with more valence electrons such as VASP's GW potentials"
            )

        # Now we want to label our valence features as Covalent, Metallic, or bare electron.
        # Many covalent and metallic features are easy to find. Covalent bonds
        # are typically exactly along a bond between an atom and its nearest
        # neighbors. Metallic features have a low depth. We mark these first
        graph = self.mark_metallic_covalent_easy(
            bader,
            graph,
            metal_depth_cutoff=metal_depth_cutoff,
            min_covalent_angle=min_covalent_angle,
            min_covalent_bond_ratio=min_covalent_bond_ratio,
        )

        # Now we calculate a bare electron indicator for each valence basin. This
        # is used just to give a sense of how bare an electron is.
        graph = self.mark_electride_character(graph)

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

    def mark_atomic_basins(
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
            # may only have a single reducible feature. We check for this by
            # noting if the child features fully surround an atom at the ELF they separate at
            # NOTE: -1 atoms really indicates infinite
            elif num_atoms > 1 or num_atoms == -1:  # and remaining_atoms > 0:
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
            # The final option is that our reducible region surrounds exactly
            # one atom. This would be the correct way to distinguish atoms if
            # we used a full electron method. Most of the subregions of this
            # environment will be atomic, but they can be of several types including
            # atom shells/cores, unshared electrons, lone-pairs. The one exception
            # is heterogenous covalent bonds, which should be shared.
            elif num_atoms == 1:
                # first we check that this reducible region isn't itself a child
                # of a reducible region with 1 atom. If it's not we note that
                # we've found an atom
                parent = graph.parent_dict(i)
                if "split" in parent.keys():
                    if not parent["atom_num"] == 1:
                        remaining_atoms -= 1
                # Now we loop over each child and check if they are a core/shell
                # reducible region, or other. If we have lone pairs, we will have
                # one core/reducible region and one or two others. If we have
                # covalent regions we will have only others. If we have only
                # core/shell/reducible regions, we will have no others
                # 0=reducible, 1=shell, 2=core, 3=other, 4=lone-pair 5=covalent
                assignments = []
                child_indices = []
                for child_idx, child in graph.child_dicts(i).items():
                    child_indices.append(child_idx)
                    # If we have a split, this region is further reducible
                    if "split" in child.keys():
                        assignments.append(0)
                        continue
                    # If we have many shell basins that form a sphere around the
                    # atom they may separate at a low depth.
                    if child["depth"] < shell_depth:
                        assignments.append(1)
                        continue
                    # otherwise, we check if the feature surrounds an atom
                    # Get the basins that belong to this child
                    basins = child["basins"]
                    # Using these basins, and the value the basin split at, we
                    # get a mask for the location of the basin
                    parent_split = node["split"]
                    low_elf_mask = np.isin(basin_labeled_voxels, basins) & np.where(
                        elf_data > parent_split, True, False
                    )
                    atoms_in_basin = self.get_atoms_surrounded_by_volume(low_elf_mask)
                    if len(atoms_in_basin) > 0:
                        # We have an core/shell region
                        assignments.append(2)
                    else:
                        # otherwise its an other
                        assignments.append(3)
                # Now we have all of our assignments at this level. If we have
                # an other assignment, we want to see what other types of assignments
                # we have. If the only other assignment is a core, this must be a
                # lone pair. If there are only "other" assignments, we either have
                # covalent bonds or a mix of covalent bonds and lone-pairs. There
                # is a special case where we have an "other" assignment and a
                # reducible feature. This reducible feature may be made of of
                # "others" or it might contain a core. If it contains "others" we
                # want to label these here as they may be lone-pairs. To do this,
                # we update our assignments if needed
                assignments = np.array(assignments)
                child_indices = np.array(child_indices)
                new_assignments = []
                new_children = []
                if 3 in assignments and 0 in assignments:
                    for child_idx, assignment in zip(child_indices, assignments):
                        if assignment == 0:
                            # check if we have any atoms in this reducible feature
                            child_node = graph.nodes[child_idx]
                            child_atom_num = child_node["atom_num"]
                            if child_atom_num == 0:
                                # We have a core and leave it be
                                new_children.append(child_idx)
                                new_assignments.append(assignment)
                            else:
                                # We have other features and want to label them all
                                # as such.
                                for subchild_idx, subchild in graph.deep_child_dicts(
                                    child_idx
                                ).items():
                                    if "split" in subchild.keys():
                                        continue
                                    new_children.append(subchild_idx)
                                    new_assignments.append(3)
                        else:
                            new_children.append(child_idx)
                            new_assignments.append(assignment)
                    # Combine our new assignments and children
                    assignments = np.array(new_assignments, dtype=int)
                    child_indices = np.array(new_children, dtype=int)

                # Now we check our assignments
                if 3 in assignments:
                    if len(np.unique(assignments)) == 1:
                        # we only have covalent bonds. Replace all others
                        assignments = np.where(assignments == 3, 5, assignments)
                    else:
                        # We have both others and something else, i.e. a lone pair.
                        # Replace all others with lone pairs
                        assignments = np.where(assignments == 3, 4, assignments)
                # Now we should be able to label all of our children
                for assignment, child_idx in zip(assignments, child_indices):
                    # for assignment, child_idx in zip(assignments, graph.child_indices(i)):
                    basin_type = "atom"
                    if assignment == 0:
                        continue
                    elif assignment == 1:
                        basin_subtype = "shell"
                    elif assignment == 2:
                        basin_subtype = "core"
                    elif assignment == 4:
                        basin_type = "val"
                        basin_subtype = "lone-pair"
                    elif assignment == 5:
                        basin_type = "val"
                        basin_subtype = "covalent"
                    networkx.set_node_attributes(
                        graph,
                        {child_idx: {"type": basin_type, "subtype": basin_subtype}},
                    )
        return graph

    def mark_metallic_covalent_easy(
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
            current_subtype = attributes.get("subtype")
            if current_subtype == "lone-pair":
                continue
            # Default to bare electron
            basin_type = "val"
            subtype = "bare electron"
            # first check for metallic character as this is easy. Note we make
            # sure this feature isn't already assigned as covalent to avoid relabeling
            # features that have already been found
            if (
                attributes["depth"] < metal_depth_cutoff
                and current_subtype != "covalent"
            ):
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
            # Finally, there are a couple of exceptions, particularly for low
            # pseudopotential situations related to lone pairs.
            # Covalent bonds and lone-pair may
            # form a feature surrounding an atom (e.g. CO2). When this happens
            # they might both be marked as covalent during the atom marking.
            # However, the lone pairs won't be marked as covalent here, so we
            # relabel them.
            if current_subtype == "covalent" and not covalent:
                subtype = "lone-pair"  # gets set later
            # Additionally, if the covalent/lone-pair feature surround two atoms
            # they will both be labeled initially as valent, but not covalent.
            # This happens in CaC2 around the C2 molecules for example. The
            # covalent one will be labeled in the next line, but the lone-pair will
            # be mislabeled still as a bare electron. We correct for this in an
            # additional loop by checking for bare electrons that are siblings with
            # covalent bonds.
            if covalent:
                subtype = "covalent"
            # We've now checked for metallic character and covalent bonds. We update
            # our subtype accordingly
            networkx.set_node_attributes(
                graph, {feature_idx: {"type": basin_type, "subtype": subtype}}
            )
        # Now we check for mislabeled lone-pairs as mentioned above.
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

    def mark_electride_character(self, graph: BifurcationGraph()) -> BifurcationGraph():
        """
        Takes in a bifurcation graph and calculates an electride character
        score for each unlabeled valence feature. Electride character ranges from
        0 to 1 and is the combination of several different metrics:
        ELF value, charge, depth, volume, and atom distance.
        """
        valence_summary = self.get_valence_summary(graph)
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
            hydride_radius = 2.08  # Taken from wikipedia and subject to change
            hydride_volume = 4 / 3 * 3.14159 * (hydride_radius**3)
            volume_contribution = min(attributes["volume"] / hydride_volume, 1)

            # Next is the distance from the atom. Ideally this should be scaled
            # relative to the radius of the atom, but which radius to use is a
            # difficult question. We use CrystalNN to get the neighbors around
            # the nearest atom and get the EN difference. We use this to guess
            # whether covalent or ionic radii should be used, then pull the appropriate one.
            atom_idx = attributes["nearest_atom"]
            atom_radius = self.get_atom_radius_guess(atom_idx)
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
        **cutoff_kwargs,
    ):
        """
        Plots bifurcation plots automatically. Graphs will be generated
        automatically using the provided resolution. If the provided
        ELF and Charge Density are spin polarized, two plots will be
        generated.
        """

        if self.spin_polarized:
            graph_up, graph_down = self.get_bifurcation_graphs(
                resolution,
                **cutoff_kwargs,
            )
            plot_up = self.get_bifurcation_plot(graph_up)
            plot_down = self.get_bifurcation_plot(graph_down)
            return plot_up, plot_down
        else:
            graph = self.get_bifurcation_graphs(resolution, **cutoff_kwargs)
            return self.get_bifurcation_plot(graph)

    def get_bifurcation_plot(self, graph: BifurcationGraph()):
        """
        Plots a bifurcation graph.
        """
        labels = networkx.get_node_attributes(graph, "label")
        pos = networkx.multipartite_layout(graph)
        pos_xs = []
        for key, value in pos.items():
            pos_xs.append(value[0])
        pos_xs = np.array(pos_xs).round(2)
        xs, counts = np.unique(pos_xs, return_counts=True)
        y_scale = counts.max()
        y_size = y_scale / 0.75
        x_size = y_size * 4 / 3

        # Draw the graph
        fig = plt.figure(figsize=(x_size, y_size))
        ax = fig.add_subplot()
        networkx.draw(
            graph, pos, node_color="lightblue", edge_color="gray", ax=ax
        )  # , node_size=2000, font_size=12,ax=ax)
        networkx.draw_networkx_labels(
            graph, pos, labels, font_color="black", ax=ax
        )  # , font_size=12
        fig.tight_layout()
        # Show plot
        plt.show()
        return plt

    def get_electride_structures(
        self,
        resolution: float = 0.02,
        include_lone_pairs: bool = False,
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
            structure_up = self._get_electride_structure(
                graph_up,
                self.bader_up,
                include_lone_pairs,
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            )
            structure_down = self._get_electride_structure(
                graph_down,
                self.bader_down,
                include_lone_pairs,
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
            return self._get_electride_structure(
                graph,
                self.bader_up,
                include_lone_pairs,
                electride_elf_min,
                electride_depth_min,
                electride_charge_min,
                electride_volume_min,
                electride_radius_min,
            )

    def _get_electride_structure(
        self,
        graph: BifurcationGraph(),
        bader,
        include_lone_pairs: bool = False,
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
                species = "Z"
            elif subtype == "metallic":
                species = "m"
            elif subtype == "lone-pair":
                if include_lone_pairs:
                    species = "lp"
                else:
                    # skip to next feature
                    continue
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
        return structure

    # def get_atomic_basins(self, start_elf = 0, end_elf = 0.25, increment=0.01):
    #     """
    #     This method performs the first basin labelling process. Starting
    #     from zero and increasing in small increments, the ELF first splits
    #     into atomic features (core electrons and lone pairs) and non-atomic
    #     features (electrides, covalent bonds, metal bonds). At slightly
    #     higher ELF values, atomic features will split into core electrons
    #     and lone pairs. At even higher values, the non-atomic features
    #     will split, but they are topologically similar so we use other
    #     methods to label them later on.

    #     Atomic features are labeled with a 1, while unassigned features
    #     are labeled with a 0.
    #     """
    #     #######################################################################
    #     # first we create an array that we will use to keep track of our assigned
    #     # basins. 0 will be unassigned, 1 will be an atom.
    #     # At this point, unassigned will be the same as non-atomic basins
    #     #######################################################################
    #     basin_type_assignments = np.zeros(len(self.basin_elf_values))
    #     basin_atom_assignments = basin_type_assignments - 1
    #     elf_grid = self.elf_grid.copy()
    #     elf_data = elf_grid.total
    #     basin_labels = self.basin_labeled_voxels
    #     # basin_closest_atom = self.bader.bader_atoms.copy()

    #     #######################################################################
    #     # Now we apply some ideas from catastrophe theory. We start at a low
    #     # ELF and increase incrementally. At each increase we remove any volume
    #     # at below our ELF value. This leaves a 3D volume. As we increase, this
    #     # volume will split into several volumes. If a new volume contains only
    #     # one atom it is considered atomic. If it contains multiple atoms we need
    #     # to increase the ELF more to find these atomic basins.
    #     #######################################################################
    #     for i in range(round((end_elf-start_elf)/increment)):
    #         # get our data, replacing any values below our cutoff with 0
    #         elf_cutoff = start_elf + i*increment
    #         cutoff_elf_grid = np.where(elf_data >= elf_cutoff, 1, 0)
    #         # label our data to get the unique features
    #         label_structure = np.ones([3,3,3])
    #         featured_grid, _ = label(cutoff_elf_grid, label_structure)

    #         # Features connected through opposite sides of the unit cell should
    #         # have the same label, but they don't currently. To handle this, we
    #         # pad our featured grid, re-label it, and check if the new labels
    #         # contain multiple of our previous labels.
    #         featured_grid = self.wrap_labeled_grid(featured_grid)

    #         # Now we want to see if any of the features contain exactly one atom.
    #         # If they do, we label them as core basins for now.
    #         # BUG: In small unit cells there may be a point where one atom splits
    #         # off but another hasn't. If the unsplit atom is in the center of
    #         # the unit cell this algorithm will consider all of the valence basins
    #         # to be part of it, even though the feature connects to the same
    #         # atom a unit cell over.
    #         for j in range(len(np.unique(featured_grid))):
    #             mask = featured_grid == j
    #             # atom_count = 0
    #             # atom_value = 0
    #             # for atom_idx, atom_sphere_coords in enumerate(self.site_sphere_voxel_coords):
    #             #     atom_sphere_in_feature = np.where(
    #             #         mask[
    #             #         atom_sphere_coords[:, 0],
    #             #         atom_sphere_coords[:, 1],
    #             #         atom_sphere_coords[:, 2],
    #             #     ])[0]
    #             #     if len(atom_sphere_in_feature) > 0:
    #             #         atom_count += 1
    #             #         atom_value = atom_idx

    #             atom_values = self.get_atoms_in_volume(mask)
    #             atom_count = len(atom_values)

    #             if atom_count == 1:
    #                 # check which basins overlap with this feature. Assign these
    #                 # as core basins
    #                 included_basins = np.unique(basin_labels[mask])
    #                 basin_type_assignments[included_basins] = 1
    #                 # Also assign the basins to the nearest atom
    #                 basin_atom_assignments[included_basins] = atom_values[0]
    #                 # add assigned basins to this loops list
    #                 # current_assigned_basins=np.concatenate([current_assigned_basins, included_basins])

    #     # BUG: Covalent structures without enough valence electrons will assign
    #     # the covalent bonds to an atom with this setup.

    #     # We've now assigned all our atomic basins. We confirm that we have at
    #     # least one assignment for every atom
    #     for site_idx, site in enumerate(self.structure):
    #         site_basins = np.where(basin_atom_assignments==site_idx)[0]
    #         if len(site_basins) == 0:
    #             raise Exception(
    # "At least one atom was not assigned a zero-flux basin. This typically results"
    # "from pseudo-potentials (PPs) with only valence electrons (e.g. the defaults for Al, Si, B in VASP 5.X.X)."
    # "Please use PPs with more valence electrons such as VASP's GW potentials"
    #             )

    #     # !!! It may be useful to mark lone pairs somehow.

    #     return basin_type_assignments, basin_atom_assignments

    # def get_metal_bonds(
    #         self,
    #         atom_assignments,
    #         electride_finder_cutoff: float = 0.5,
    #         ):
    #     """
    #     This method assigns shared metal basins. This is done using
    #     a cutoff in the ELF. It should be noted that this may not capture
    #     all users ideas of metal bonds vs. electrides as the
    #     difference between the two should probably be viewed as a spectrum
    #     rather than a hard cutoff.

    #     Shared bonds are noted with a 2.
    #     """
    #     # get which indices aren't assigned yet
    #     unassigned_maxima_indices = np.where(atom_assignments==0)[0]
    #     # get the ELF values at these maxima and find which ones are below the
    #     # cutoff, then assign.
    #     elf_values = self.basin_elf_values[unassigned_maxima_indices]
    #     assignment_mask = np.where(elf_values < electride_finder_cutoff, 2, 0)
    #     atom_assignments[unassigned_maxima_indices] = assignment_mask

    #     return atom_assignments

    # def get_covalent_bonds(
    #         self,
    #         atom_assignments,
    #         ):
    #     """
    #     This method assigns shared basins that are directly along
    #     2-center bonds. This can include both metal and covalent bonds.

    #     Shared bonds are noted with a 2.
    #     """
    #     # First, we get the coordinates of each site and its closest neighbors
    #     all_neighbors = PartitioningToolkit(
    #         self.elf_grid,
    #         self.bader,
    #     ).all_site_neighbor_pairs.copy()
    #     site_indices = []
    #     neigh_indices = []
    #     site_coords = []
    #     neigh_coords = []
    #     site_neigh_dists = []
    #     for i, site in enumerate(self.structure):
    #         site_df = all_neighbors.loc[all_neighbors["site_index"] == i].copy()
    #         min_dist = min(site_df["dist"].to_list())
    #         site_df = site_df.loc[site_df["dist"] == min_dist]
    #         site_indices.append(np.array(site_df["site_index"].to_list()))
    #         neigh_indices.append(np.array(site_df["neigh_index"].to_list()))
    #         site_coords.append(np.array(site_df["site_coords"].to_list()))
    #         neigh_coords.append(np.array(site_df["neigh_coords"].to_list()))
    #         site_neigh_dists.append(np.array(site_df["dist"].to_list()))
    #     # convert to arrays
    #     site_indices = np.concatenate(site_indices)
    #     neigh_indices = np.concatenate(neigh_indices)
    #     site_coords = np.concatenate(site_coords)
    #     neigh_coords = np.concatenate(neigh_coords)
    #     site_neigh_dists = np.concatenate(site_neigh_dists)
    #     # For each maximum, we check if it is along one of the site neighbor bonds.
    #     # We do this by getting the distance from the maximum to the site and
    #     # to the neighbor and summing the distances. If the maximum is on the line
    #     # this will be the same as the distance between the site and its neighbor.
    #     # We also keep track of which atoms the covalent bond is between
    #     unassigned_basin_indices = np.where(atom_assignments==0)[0]
    #     cart_coords = self.basin_cart_coords[unassigned_basin_indices]
    #     assignments = []
    #     for maximum_coord in cart_coords:
    #         # calculate the distance from the maximum to the site and to the
    #         # neighbor
    #         max_to_site_dist = np.linalg.norm(site_coords - maximum_coord, axis=1)
    #         max_to_neigh_dist = np.linalg.norm(neigh_coords - maximum_coord, axis=1)
    #         # calculate the total distance
    #         total_dist = np.round(max_to_site_dist + max_to_neigh_dist, 5)
    #         # Check if the distances total from the maximum to the site and neighbor
    #         # are the same as the total distance from the site to the neighbor (within
    #         # a tolerance of 0.1A)
    #         condition_array1 = site_neigh_dists - 0.1 < total_dist
    #         condition_array2 = total_dist < site_neigh_dists + 0.1
    #         if np.any(condition_array1 & condition_array2):
    #             # We have a shared bond. Add it to our assignments
    #             assignments.append(2)
    #         else:
    #             assignments.append(0)
    #     # update assignments and return
    #     atom_assignments[unassigned_basin_indices] = assignments
    #     return atom_assignments

    # def get_electride_structure(
    #         self,
    #         electride_finder_cutoff: float = 0.5,
    #         # electride_size_cutoff: float = 0.1,
    #         ignore_low_pseudopotentials: bool = False,
    #         dont_label_shared: bool = False,
    #         ):
    # """
    # The assignment of ELF basins to important chemical features through
    # topological analysis is a well studied subject. A very thorough
    # discussion can be found from C. Gatti in his article titled
    # Chemical bonding in crystals: new directions
    # (Z. Kristallogr. 220 (2005) 399-457)

    # Broadly, the ELF can be divided into basins following a similar
    # method to that proposed by Bader (QTAIM). Each basin consists
    # of a maximum (attractor) and a zero-flux surface (seperatrix)
    # seperating it from adjacent basins. These basins can be categorized
    # into two main types: core basins and valence basins. The core
    # basins consist of spherical attractors surrounding the nucleus
    # of an atom. The valence basins can be broken up into a number of
    # things including ionic-like or van der Waals-like interactions,
    # covalent bonds, lone pairs, f-centers and electrides. These
    # features can be distinguished by their location, shape, and
    # "synaptic order". Synaptic order refers to the number of core
    # basins bordering the valence basin. Unfortunately, it can be
    # quite difficult to automatically distinguish a core basin from
    # an ionic/vdw like basin, especially when using pseudopotentials.
    # Therefore, we don't use synaptic order to distinguish valence
    # basins though this is a common practice, particularly in the
    # molecular community.

    # Another useful method that aids in distinguishing basin types
    # is the use of f-localization domains. This is the region bounded
    # by the isosurface at ELF = f. All systems have a low f value
    # where there is a single composite "parent" domain. Incrementally
    # increasing f first results in the parent domain splitting into
    # core domains and a single valence domain containing all the
    # valence attractors. This valence domain has as many holes as
    # there are atomic cores. Increasing f further will result in
    # the existing domains further splitting. A domain is considered
    # reducible if it contains multiple attractors and irreducible if
    # it has only 1. One may order the f values at which reducible
    # domains split until all domains are irreducible at a high f value.
    # These splitting points can be organized into a tree diagram
    # representing the hierarchy of basins. For example:

    #                          \-core-basin
    #                          \
    #         \-atom-basins----\
    #         \                \
    #         \                \-lone-pair
    # parent--\
    #         \                \-Electrides
    #         \                \
    #         \-Valence-basins-\                         \-metal-bond1
    #         \                \                         \
    #                          \-Metal-bond-"superbasin"-\
    #                                                    \
    #                                                    \-metal-bond2

    # In principle, a thorough analysis of the ELF should be done on
    # ELF calculated using all of the electrons in the system. In
    # practice, this can be difficult, especially given the prevalence
    # of packages like VASP which utilize a frozen core to enhance
    # calculation efficiency. This issue also results in increased
    # difficulty in determining synaptic order. Thus we try and distinguish
    # the key basin types as follows:

    #     Core Basins or Ionic/VDW-like basins: These basins can be
    #     particularly hard to distinguish from each other, which causes
    #     the difficulty calculating synaptic order. They fully
    #     surround the nucleus of an atom in a sphere-like or nearly
    #     sphere-like manor.

    #     Lone-pair basins: These basins are monosynaptic. When the
    #     f-domain first splits into atom and valence regions, they
    #     tend to remain connected to the atom core.

    #     Covalent basins: Unlike lone-pairs or ionic/vdw basins,
    #     these basins sit in the valence domain when the f-domain
    #     first splits at low f values. They also tend to have high
    #     ELF values and sit directly along a 2-center bond.

    #     Metallic basins: Similar to covalent basins, these basins
    #     sit in the valence domain when the f-domain first splits.
    #     From my experience they tend to form in one of two manors.
    #     In the first they form as one maximum directly between a
    #     2-center bond. In this situation they tend to have reasonably
    #     high ELF values. In the second, they form several shallow
    #     attractors with values very close to the separatrices between
    #     them. In this situation they typically have low ELF values
    #     and may be more conveniently considered as one "superbasin"
    #     or "basin set".

    #     Electride/F-center basins: These basins are similar to
    #     covalent and metallic bonds but are distinct in that they
    #     do not lay directly along bonds. They also don't form as
    #     shallow of attractors as metal basins might.

    # There may be other additional types of basins, but these are
    # by far the most common in our use-case. We will divide these
    # into three categories for the sake of assigning charge:

    #     1. Atomic basins. These include cores, ionic/vdw, and lone-
    #     pairs. These are separated from the other types of basins
    #     when the f-domain first starts to split, so they are easiest
    #     to handle first. Since all of the charge of these basins
    #     will be assigned to the atomic basin regardless, we do not
    #     distinguish between them. These will be labeled with a 1.

    #     2. Shared basins. This includes covalent bonds and metal bonds.
    #     For our use, these will be determined as either basins
    #     sitting directly along a 2-center bond or as attractors that
    #     have a low ELF value as determined by a cutoff. We will also
    #     track which atoms these basins directly border. These will
    #     be labeled with a 2.

    #     3. Electrides/F-centers. These basins don't belong to any
    #     atom and will be marked as their own entities. They are
    #     essentially anything left over from the previous two assignments.
    #     These will be labeled with a 3.

    # It should be noted that this is not a perfect method and more
    # complex situations may not be well represented (e.g. multi-center
    # bonds, highly localized metal bonds, etc.)

    # The returned structure will add dummy atoms representing shared
    # basins (Z) and electrides (X).
    # """
    #     #######################################################################
    #     # Step 1: Assign atomic basins.
    #     # This first step is important to establish what basins are considered
    #     # part of the "core". Unfortunately, due to the use of pseudopotentials
    #     # we may not always have one. This can be ok so long as we have an ionic
    #     # bond around our nucleus allowing us to separate shared basins and
    #     # electrides from the atom center. We will raise an exception if this is
    #     # not the case.
    #     #######################################################################

    #     # Get an array representing the types of atom basins found so far. The
    #     # array is the same length as the total number of basins with the following
    #     # values: 0: no assignment, 1: atom basin
    #     atom_assignments, _ = self.get_atomic_basins()

    #     #######################################################################
    #     # Step 2: Assign shared basins that have low ELF values
    #     #######################################################################
    #     atom_assignments = self.get_metal_bonds(atom_assignments, electride_finder_cutoff)

    #     #######################################################################
    #     # Step 3: Assign shared basins that lie directly along a 2-center bond
    #     #######################################################################
    #     atom_assignments = self.get_covalent_bonds(atom_assignments)

    #     #######################################################################
    #     # Step 4: Assign electride basins
    #     #######################################################################
    #     # anything left is considered an electride
    #     atom_assignments = np.where(atom_assignments==0, 3, atom_assignments)

    #     #######################################################################
    #     # Step 5: Create structure
    #     #######################################################################
    #     new_structure = self.structure.copy()
    #     for i, assignment in enumerate(atom_assignments):
    #         frac_coords = self.basin_frac_coords[i]
    #         if assignment == 2:
    #             if not dont_label_shared:
    #                 # we have a shared basin
    #                 new_structure.append("Z", frac_coords)
    #         elif assignment == 3:
    #             # we have an electride
    #             new_structure.append("X", frac_coords)

    #     # combine any maxima that are very close and likely seperated due to
    #     # voxelation
    #     tol = self.elf_grid.max_voxel_dist * 2
    #     new_structure.merge_sites(tol=tol, mode="average")

    #     logging.info(
    #         f"{len(new_structure.indices_from_symbol('X'))} electride sites found."
    #     )
    #     # Get atoms involved in each bond
    #     coord_envs = []
    #     shared_bonds_indices = new_structure.indices_from_symbol("Z")
    #     if len(shared_bonds_indices) > 0:
    #         logging.warning(
    #             f"{len(new_structure.indices_from_symbol('Z'))} covalent/metallic bonds found. Bonds will be seperated using zero-flux surface and oxidation states won't make sense"
    #         )

    #         #######################################################################
    #         # Step 5: Get bonded atoms
    #         #######################################################################

    #         cnn = CrystalNN()
    #         for i in shared_bonds_indices:
    #             # create a temporary structure and append a dummy hydride to
    #             # represent the bond
    #             temp_structure = self.structure.copy()
    #             temp_structure.append("H-", new_structure.frac_coords[i])
    #             # For most covalent structures and electrides, CrystalNN won't
    #             # find appropriate radii and will instead use covalent/atomic
    #             # radii. This will raise a warning, but we can't do much about it
    #             # easily. We ignore the warning here.
    #             with warnings.catch_warnings():
    #                 warnings.filterwarnings(
    #                     "ignore", category=UserWarning, module="pymatgen"
    #                 )
    #                 neighbors = cnn.get_nn(temp_structure, -1)
    #             neigh_indices = []
    #             for neigh in neighbors:
    #                 neigh_indices.append(neigh.index)
    #             coord_envs.append(neigh_indices)

    #     return new_structure, coord_envs

    @classmethod
    def from_files(
        cls,
        directory: Path = Path("."),
        elf_file: str = "ELFCAR",
        charge_file: str = "CHGCAR",
        allow_spin: bool = False,
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
            allow_spin (bool):
                Whether to check for spin and provider results for both. If this
                is False, only the first set of data in the provided files is
                used.

        Returns:
            A ElectrideFinder instance.
        """

        elf_grid = Grid.from_file(directory / elf_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return ElectrideFinder(
            elf_grid=elf_grid,
            charge_grid=charge_grid,
            directory=directory,
            allow_spin=allow_spin,
            ignore_low_pseudopotentials=ignore_low_pseudopotentials,
        )
