# -*- coding: utf-8 -*-
import logging
import math
from functools import cached_property
from itertools import product
from pathlib import Path

import numpy as np
import psutil
from networkx.utils import UnionFind
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from scipy.ndimage import label
from tqdm import tqdm

from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit


class ElectrideFinder:
    """
    A class for finding electride sites from an ELFCAR.

    Args:
        grid : Grid
            A BadELF app Grid instance made from an ELFCAR.
    """

    def __init__(
        self,
        grid: Grid,
        directory: Path,
    ):
        self.grid = grid.copy()
        self.directory = directory

    @cached_property
    def local_maxima(self):
        """
        The local maxima in a 3D numpy array
        """
        return self.find_local_maxima()

    def find_local_maxima(self, neighborhood_size: int = 2, threshold: float = 0.5):
        """
        Find local maxima in a 3D numpy array.

        Args:
            neighborhood_size (int):
                Size of the neighborhood for finding local maxima
            threshold (float):
                Threshold for considering a point as a local maximum

        Returns:
            List of tuples containing the fractional coordinates of local maxima
        """
        grid = self.grid.copy()
        # grid.regrid(desired_resolution=1000)
        elf_data = grid.total
        # get the indices and values
        voxel_coords = np.indices(elf_data.shape).reshape(3, -1).T
        voxel_values = elf_data.ravel()
        # get the transforms required to move the voxels to the voxels in a neighborhood
        # around them
        number_range = [i for i in range(-neighborhood_size, neighborhood_size + 1)]
        transforms = list(product(number_range, repeat=3))
        # Get padded data so that we can look at voxels at the edges
        padded_elf_data = np.pad(elf_data, neighborhood_size, mode="wrap")
        padded_voxel_coords = voxel_coords + neighborhood_size
        # For each transformation, get the value of the neighboring voxel
        surrounding_values = []
        for trans in transforms:
            trans = np.array(trans)
            new_voxel_coords = padded_voxel_coords + trans
            surrounding_values.append(
                padded_elf_data[
                    new_voxel_coords[:, 0],
                    new_voxel_coords[:, 1],
                    new_voxel_coords[:, 2],
                ]
            )
        surrounding_values = np.column_stack(surrounding_values)
        # find the maximum voxel in the surrounding area
        max_values = np.max(surrounding_values, axis=1)
        maxima_mask = np.where(voxel_values == max_values, voxel_values, 0)
        maxima_mask = np.where(maxima_mask >= threshold, True, False)
        maxima_vox_coords = voxel_coords[maxima_mask]
        # convert to fractional coords
        maxima_frac_coords = grid.get_frac_coords_from_vox_full_array(maxima_vox_coords)
        # create a dummy structure and merge nearby maxima
        maxima_structure = grid.structure.copy()
        maxima_structure.remove_species(maxima_structure.symbol_set)
        for frac_coord in maxima_frac_coords:
            maxima_structure.append("He", frac_coord)
        tol = grid.max_voxel_dist * 2
        maxima_structure.merge_sites(tol=tol, mode="average")
        new_maxima_frac_coords = maxima_structure.frac_coords
        # sometimes the pymatgen merge_sites method will return 1 instead of zero
        # for a fractional coordinate. We convert these to 0 here.
        new_maxima_frac_coords = np.where(
            new_maxima_frac_coords == 1, 0, new_maxima_frac_coords
        )
        new_maxima_frac_coords = new_maxima_frac_coords.round(5)
        # maxima_cart_coords = grid.get_cart_coords_from_vox_full_array(maxima_vox_coords)
        return new_maxima_frac_coords  # , maxima_values

    @cached_property
    def elf_radii(self):
        """
        Gets the elf radius of each atom in the structure. This is no longer
        used in this algorithm, but may be a useful method in the future.

        Returns:
            A dictionary connecting atomic sites to their elf ionic radii
        """
        grid = self.grid.copy()
        structure = grid.structure.copy()
        # We don't want to find the radius for every atom in the structure if
        # there is symmetry. We instead find the radius for each unique atom
        symmetry_dataset = SpacegroupAnalyzer(structure).get_symmetry_dataset()
        equivalent_atoms = symmetry_dataset["equivalent_atoms"]

        # We now have an array of the same length as the structure. Each value
        # in the array is an int pointing to the first equivalent atom in the
        # structure if it exists (or itself if its the earliest equivalent one).
        # Now we want to get the ELF radius for each unique atom. We iterate over
        # each unique atom to get its radius and add it to a dictionary.
        partitioning_toolkit = PartitioningToolkit(grid)
        unique_atoms = np.unique(equivalent_atoms)
        unique_atom_radii = {}
        for atom in unique_atoms:
            radius = partitioning_toolkit.get_elf_ionic_radius(
                site_index=atom,
                structure=structure,
            )
            unique_atom_radii[atom] = radius

        # We now construct an array for all of the atoms in the structure
        all_atom_radii = []
        for site_index, site in enumerate(structure):
            equiv_atom = equivalent_atoms[site_index]
            radius = unique_atom_radii[equiv_atom]
            all_atom_radii.append(radius)
        all_atom_radii = np.array(all_atom_radii)

        return all_atom_radii

    def get_electride_structure(
        self,
        electride_finder_cutoff: float = 0.5,
        electride_size_cutoff: float = 0.1,
        threads: int = None,
        check_for_covalency: bool = True,
    ):
        """
        Finds the electrides in a structure using an ELF grid.

        Args:
            electride_finder_cutoff (float):
                The minimum elf value at the site to be considered a possible
                electride. The default is 0.5.

            electride_size_cutoff (float):
                The minimum size an electride site must be to be counted. This
                mainly intended to remove any sites that are potentially just
                features of the voxel grid and should be quite small.

            threads (int):
                The number of threads to use to perform the bader/zero-flux
                calculation.

            check_for_covalency (bool):
                Whether to prevent a structure from being found if covalency is
                found in the structure. It is highly recommended to keep this as
                True as there is currently no method implemented to handle
                covalency.

        Returns:
            A structure object with the found electride sites labeled with "He"
            dummy atoms.
        """
        ###############################################################################
        # This part of the code runs zero-flux partitioning on the ELF and records the
        # basins
        ###############################################################################
        # Get the basins and assigned voxels
        elf_grid = self.grid.copy()
        local_maxima = self.find_local_maxima(threshold=electride_finder_cutoff)
        threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        bader = elf_grid.run_pybader(threads)

        # Get the voxel indices for each found maxima
        basin_maxima_vox_coords = elf_grid.get_vox_coords_from_frac_full_array(
            bader.bader_maxima_fractional
        ).astype(int)
        # Get the ELF values for the maxima
        basin_maxima = elf_grid.total[
            basin_maxima_vox_coords[:, 0],
            basin_maxima_vox_coords[:, 1],
            basin_maxima_vox_coords[:, 2],
        ]
        # Get the closest atom to each maxima
        basin_closest_atom = bader.bader_atoms.copy()
        # Get the voxel basin assignments
        basin_labeled_voxels = bader.bader_volumes.copy()
        # Get the structure
        structure = elf_grid.structure
        # Get the data array
        elf_data = elf_grid.total
        ###############################################################################
        # This part of the code creates a supercell of the data so that it is easy to
        # determine if different basins are connected in the next step
        ###############################################################################
        logging.info("Making supercells")
        supercell_elf_data = elf_grid.get_2x_supercell(elf_data)
        supercell_label_data = elf_grid.get_2x_supercell(basin_labeled_voxels).astype(
            int
        )

        ###############################################################################
        # This part of the code isolates the basins that would be assigned to each atom.
        # It checks what the ELF value at each maxima is. Then, starting from the highest
        # value it checks if these maxima's isosurfaces would connect with a very slight
        # decrease in the ELF value.
        ###############################################################################
        logging.info("connecting voxelated basins")
        # Create a UnionFind class to keep track of each of our connections
        connections = UnionFind()
        for i, site in tqdm(enumerate(structure), total=len(structure)):
            site_maxima = np.where(basin_closest_atom == i)[0]
            site_basin_maxima = basin_maxima[site_maxima]
            # site_supercell_elf_data = np.where(np.isin(supercell_label_data,site_maxima),supercell_elf_data,0)
            # Get each unique maximum ELF value
            unique_maxima = np.flip(np.unique(site_basin_maxima))
            # We want to reduce the total number of maxima we need to scan through.
            # To do this, we look at which maxima are found above a value slightly
            # below the highest ELF. If any maxima other than those at the highest
            # ELF are found we expand out search slightly lower and repeat until
            # no new peaks are found. Then we continue to the next highest ELF value
            # that hasn't been assigned.
            maxima_to_search = []
            for max_elf in unique_maxima:
                all_maxima = False
                # Get the number of maxima at this ELF value
                num_of_maxima_values = len(np.where(site_basin_maxima == max_elf)[0])
                while not all_maxima:
                    # Get the number of maxima slightly below this value then check
                    # if it is the same as our starting number of maxima
                    contained_maxima_values = site_basin_maxima[
                        site_basin_maxima >= max_elf - 0.05
                    ]
                    if len(contained_maxima_values) == num_of_maxima_values:
                        all_maxima = True
                    else:
                        # If the value has increased, we update our max_elf and the
                        # number of maxima
                        max_elf = contained_maxima_values.min()
                        num_of_maxima_values = len(contained_maxima_values)
                # Add the final maxima found to the maxima to search
                maxima_to_search.append(max_elf)
            maxima_to_search = np.flip(np.unique(maxima_to_search))
            # Now we search through the reduced list of maxima we found above to
            # see which basins connect slightly below their maximum ELF value
            assigned_labels = []
            for max_elf in maxima_to_search:
                # get labels with max values above max_elf-0.05.
                available_labels = np.where(site_basin_maxima >= max_elf - 0.05)[0]
                available_labels = available_labels[
                    ~np.isin(available_labels, assigned_labels)
                ]
                # We have the available labels in terms of those available for this
                # atom. We need those available from the total list of labels
                available_labels = site_maxima[available_labels]
                if len(available_labels) == 0:
                    continue
                # We add the labels at this elf maxima to our assigned labels so that we don't
                # double assign later.
                assigned_labels.extend(np.where(site_basin_maxima >= max_elf)[0])
                # Set conditions for what ELF to search for connections. The first condition
                # removes data that has elf valuse below our cutoff of max_elf-0.05. The
                # second condition removes data from basins we have already searched
                # get ELF grid with only data at max_elf-0.01 and above.
                condition1 = supercell_elf_data >= max_elf - 0.05
                condition2 = np.isin(supercell_label_data, available_labels)
                # reduce the elf data to only data matching our conditions, then get a new
                # array that is labeled with the number of features
                reduced_elf_data = np.where(
                    condition1 & condition2, supercell_elf_data, 0
                )
                label_structure = np.ones([3, 3, 3])
                featured_data, num_features = label(reduced_elf_data, label_structure)
                # Now we look at each feature
                for feature in range(num_features):
                    feature += 1
                    mask = featured_data == feature
                    connected_labels = np.unique(supercell_label_data[mask])
                    for basin_label in connected_labels[1:]:
                        connections.union(connected_labels[0], basin_label)

        ###############################################################################
        # We now have each of the basins connected after accounting for voxelation. This
        # part of the algorithm combines the connected basins and relabels them
        ###############################################################################
        # Get the sets of basins that are connected to each other
        connection_sets = list(connections.to_sets())
        for label_set in connection_sets:
            label_set = np.array(list(label_set))
            # replace all of these labels with the lowest one
            basin_labeled_voxels = np.where(
                np.isin(basin_labeled_voxels, label_set),
                label_set[0],
                basin_labeled_voxels,
            )
        # Now we reduce the labels so that they start at 0 and increase by 1 each time,
        # i.e. 0,1,2,3,etc.
        for i, j in enumerate(np.unique(basin_labeled_voxels)):
            basin_labeled_voxels = np.where(
                basin_labeled_voxels == j, i, basin_labeled_voxels
            )

        ###############################################################################
        # This section of the algorithm focuses on assigning atomic basins to atoms
        ###############################################################################
        logging.info("Finding all atomic basins")
        atom_labels = {}
        for i, site in enumerate(structure):
            atom_labels[i] = []
        # First we assign the basins that contain atoms directly
        basin_labeled_voxels += len(structure)
        for i, site in enumerate(structure):
            # Get the voxel coordinate for this site, then get the basin it
            # belongs to
            atom_voxel_coord = elf_grid.get_voxel_coords_from_frac(
                site.frac_coords
            ).astype(int)
            # Get the voxels in a sphere around the atom
            nearby_voxels = elf_grid.get_voxels_in_radius(0.3, atom_voxel_coord)
            # get the label for each of these voxel coords
            basin_labels = []
            for voxel_coord in nearby_voxels:
                basin_label = basin_labeled_voxels[
                    voxel_coord[0], voxel_coord[1], voxel_coord[2]
                ]
                basin_labels.append(basin_label)
            # Assign these basins to the site
            for basin_label in np.unique(basin_labels):
                basin_labeled_voxels = np.where(
                    basin_labeled_voxels == basin_label, i, basin_labeled_voxels
                )
        # Next we assign the basins where the maximum ELF value is less than
        # the electride finder cutoff
        basin_maxima_labels = basin_labeled_voxels[
            basin_maxima_vox_coords[:, 0],
            basin_maxima_vox_coords[:, 1],
            basin_maxima_vox_coords[:, 2],
        ]
        for basin_label in np.unique(basin_labeled_voxels)[len(structure) :]:
            # Get the ELF value at the maximum in this basin
            basin_elf_maxima = basin_maxima[
                np.where(basin_maxima_labels == basin_label)[0]
            ]
            # If the maximum is less than the cutoff (usually 0.5) assign it
            # to the closest atom
            if basin_elf_maxima.max() < electride_finder_cutoff:
                basin_atom = basin_closest_atom[
                    np.where(basin_maxima_labels == basin_label)[0]
                ][0]
                basin_labeled_voxels = np.where(
                    basin_labeled_voxels == basin_label,
                    basin_atom,
                    basin_labeled_voxels,
                )
        # Next we check the basins to see if they completely surround an atom. This will
        # only catch basins behaving like orbitals around an atom. Electrides and covalent
        # bonds have distinct maxima that don't connect all the way around an atom, even
        # if the sum of the maxima would
        supercell_label_data = elf_grid.get_2x_supercell(basin_labeled_voxels)
        for basin_label in np.unique(basin_labeled_voxels)[len(structure) :]:
            # create a super cell that is false at the basin and true elsewhere
            label_supercell = supercell_label_data != basin_label
            # find the features. If the basin surrounds an atom there should be a unique
            # feature for that atom in each quadrant of the super cell
            feature_supercell, _ = label(label_supercell)
            # Get the transformations to transform the voxel representing an atom to
            # each quadrant of the supercell
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
            for i, site in enumerate(structure):
                # Get the voxel coords of each atom in their equivalent spots in each
                # quadrant of the supercell
                frac_coords = site.frac_coords
                transformed_coords = transformations + frac_coords
                voxel_coords = elf_grid.get_vox_coords_from_frac_full_array(
                    transformed_coords
                ).astype(int)
                # Get the feature label at each transformation. If the atom is not surrounded
                # by this basin, at least some of these feature labels will be the same
                features = feature_supercell[
                    voxel_coords[:, 0], voxel_coords[:, 1], voxel_coords[:, 2]
                ]
                # print(features)
                if len(np.unique(features)) == 8:
                    # The atom is completely surrounded by this basin and the basin belongs
                    # to this atom
                    basin_labeled_voxels = np.where(
                        basin_labeled_voxels == basin_label, i, basin_labeled_voxels
                    )
                    break
        # We want to check that every atom has some assigned volume. If not, there
        # is likely covalency or a paw potential is used where there are no
        # core electrons remaining on an atom.
        if not np.all(
            np.isin([i for i in range(len(structure))], np.unique(basin_labeled_voxels))
        ):
            if check_for_covalency:
                raise Exception(
                    """At least one atom was not assigned a zero-flux basin. This can result from covalency or from pseudo-potentials with only valence electrons 
(e.g. Al, Si, B in VASP 5.X.X)."""
                )

        ###############################################################################
        # This section focuses on assigning remaining basins to electrides or covalent
        # bonds
        ###############################################################################
        # Create an empty structure to add potential electrides to
        logging.info("Assigning remaining basins to electrides or covalent bonds")
        # Create an empty structure with all of the proper lattice information
        maxima_structure = structure.copy()
        maxima_structure.remove_species(maxima_structure.symbol_set)
        final_maxima_structure = maxima_structure.copy()
        # Get the labels for each of the maxima found using pybader
        basin_maxima_labels = basin_labeled_voxels[
            basin_maxima_vox_coords[:, 0],
            basin_maxima_vox_coords[:, 1],
            basin_maxima_vox_coords[:, 2],
        ]
        # Get the fractional coordinates of each maximum
        basin_maxima_frac_coords = bader.bader_maxima_fractional
        # Find which maximum coords have not been assigned yet and add them to
        # our empty structure
        basin_maxima_frac_coords = basin_maxima_frac_coords[
            np.where(basin_maxima_labels >= len(structure))
        ]
        for frac_coord in basin_maxima_frac_coords:
            maxima_structure.append("He", frac_coord)
        # combine any maxima that may be very close to each other due to voxelation
        if len(maxima_structure) > 1:
            tol = elf_grid.max_voxel_dist * 2
            maxima_structure.merge_sites(tol=tol, mode="average")
        # reduce only to maxima found using peak finding alg
        # !!! I'm not entirely sure why this needs to happen. pybader seems to find more
        # electrides than the Henkelman group or my own algorithm.
        for frac_coord in maxima_structure.frac_coords:
            frac_coord = frac_coord.round(5)
            # sometimes the pymatgen merge_sites function returns a frac coord of
            # 1 instead of 0. We fix that here
            frac_coord = np.where(frac_coord == 1, 0, frac_coord)
            if np.any(np.all(frac_coord == local_maxima, axis=1)):
                final_maxima_structure.append("He", frac_coord)
        # Get the final cartesian coordinates for the reduced maxima
        basin_maxima_cart_coords = final_maxima_structure.cart_coords
        # Now we check if the maximum is an electride site or covalent bond
        # For now the method I'm using for if a maxima is an electride or a covalent bond
        # is simply if the maximum is along a bond between an atom and one of its closest
        # neighbors. This could be easily made a bit more involved, though it would probably
        # require running the bader algorithm again
        # First, we get the coordinates of each site and its closest neighbors
        all_neighbors = PartitioningToolkit(
            self.grid,
            bader,
        ).all_site_neighbor_pairs.copy()
        site_coords = []
        neigh_coords = []
        site_neigh_dists = []
        for i, site in enumerate(structure):
            site_df = all_neighbors.loc[all_neighbors["site_index"] == i].copy()
            min_dist = min(site_df["dist"].to_list())
            site_df = site_df.loc[site_df["dist"] == min_dist]
            site_coords.append(np.array(site_df["site_coords"].to_list()))
            neigh_coords.append(np.array(site_df["neigh_coords"].to_list()))
            site_neigh_dists.append(np.array(site_df["dist"].to_list()))
        # convert to arrays
        site_coords = np.concatenate(site_coords)
        neigh_coords = np.concatenate(neigh_coords)
        site_neigh_dists = np.concatenate(site_neigh_dists)
        # For each maximum we now check if it is along one of the site neighbor bonds.
        # We do this by getting the distance from the maximum to the site and
        # to the neighbor and summing the distances. If the maximum is on the line
        # this will be the same as the distance between the site and its neighbor
        electride_structure = structure.copy()
        for maximum_coord in basin_maxima_cart_coords:
            # calculate the distance from the maximum to the site and to the
            # neighbor
            max_to_site_dist = np.linalg.norm(site_coords - maximum_coord, axis=1)
            max_to_neigh_dist = np.linalg.norm(neigh_coords - maximum_coord, axis=1)
            # calculate the total distance
            total_dist = np.round(max_to_site_dist + max_to_neigh_dist, 5)
            # Check if the distances total from the maximum to the site and neighbor
            # are the same as the total distance from the site to the neighbor (within
            # a tolerance of 0.1A)
            condition_array1 = site_neigh_dists - 0.1 < total_dist
            condition_array2 = total_dist < site_neigh_dists + 0.1
            # If there is a covalent bond, throw an error.
            if np.any(condition_array1 & condition_array2) and check_for_covalency:
                raise Exception("Covalency found in structure")
            else:
                electride_structure.append(
                    "He", maximum_coord, coords_are_cartesian=True
                )
        # sometimes electride sites are found that are very small (i.e. < 0.1 A).
        # These are usually features of the grid and not actual electride sites
        # so we remove them. We update the elf grid with the new structure and
        # run bader
        elf_grid.structure = electride_structure
        new_bader = elf_grid.run_pybader(threads)
        # We get the voxels assigned to each site as well as the volume of a
        # single voxel.
        atoms_volumes = new_bader.atoms_volumes
        voxel_volume = new_bader.voxel_volume
        indices_to_remove = []
        for i in range(len(electride_structure)):
            # for each site, we calculate the volume assigned to them. If its
            # less than 0.1 we remove the site.
            num_voxels = len(np.where(atoms_volumes == i)[0])
            volume = num_voxels * voxel_volume
            if volume < electride_size_cutoff:
                indices_to_remove.append(i)
        electride_structure.remove_sites(indices_to_remove)
        logging.info(
            f"{len(electride_structure.indices_from_symbol('He'))} electride sites found."
        )
        # Return the electride structure
        return electride_structure
