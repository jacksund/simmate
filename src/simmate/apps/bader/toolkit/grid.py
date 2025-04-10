# -*- coding: utf-8 -*-

import itertools
import logging
from functools import cached_property
from pathlib import Path
from typing import Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from networkx.utils import UnionFind
from numpy.typing import NDArray
from pymatgen.io.vasp import VolumetricData
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import center_of_mass, label, zoom
from scipy.signal import decimate

# from scipy.ndimage import binary_erosion


class Grid(VolumetricData):
    """
    This class is a wraparound for Pymatgen's VolumetricData class with additional
    properties and methods useful to the badelf algorithm
    """

    @property
    def total(self):
        return self.data["total"]

    @total.setter
    def total(self, new_total):
        self.data["total"] = new_total

    @property
    def diff(self):
        return self.data.get("diff")

    @diff.setter
    def diff(self, new_diff):
        self.data["diff"] = new_diff

    @property
    def shape(self):
        return np.array(self.total.shape)

    @property
    def matrix(self):
        """
        A 3x3 matrix defining the a, b, and c sides of the unit cell
        """
        return self.structure.lattice.matrix

    @property
    def a(self):
        """
        The cartesian coordinates for the lattice vector "a"
        """
        return self.matrix[0]

    @property
    def b(self):
        """
        The cartesian coordinates for the lattice vector "b"
        """
        return self.matrix[1]

    @property
    def c(self):
        """
        The cartesian coordinates for the lattice vector "c"
        """
        return self.matrix[2]

    @property
    def frac_coords(self):
        """
        Array of fractional coordinates for each atom.
        """
        return self.structure.frac_coords

    @property
    def all_voxel_frac_coords(self):
        """
        The fractional coordinates for all of the voxels in the grid
        """
        a, b, c = self.shape
        voxel_indices = np.indices(self.shape).reshape(3, -1).T
        frac_coords = voxel_indices.copy().astype(float)
        frac_coords[:, 0] /= a
        frac_coords[:, 1] /= b
        frac_coords[:, 2] /= c
        return frac_coords

    @cached_property
    def voxel_dist_to_origin(self):
        frac_coords = self.all_voxel_frac_coords
        cart_coords = self.get_cart_coords_from_frac_full_array(frac_coords)
        corners = [
            np.array([0, 0, 0]),
            self.a,
            self.b,
            self.c,
            self.a + self.b,
            self.a + self.c,
            self.b + self.c,
            self.a + self.b + self.c,
        ]
        distances = []
        for corner in corners:
            voxel_distances = np.linalg.norm(cart_coords - corner, axis=1).round(6)
            distances.append(voxel_distances)
        min_distances = np.min(np.column_stack(distances), axis=1)
        min_distances = min_distances.reshape(self.shape)
        return min_distances

    @property
    def voxel_volume(self):
        """
        The volume of each voxel in the grid
        """
        volume = self.structure.volume
        voxel_num = np.prod(self.shape)
        return volume / voxel_num

    @property
    def voxel_num(self):
        """
        The number of voxels in the grid
        """
        return self.shape.prod()

    @property
    def max_voxel_dist(self):
        """
        Finds the maximum distance a voxel can be from a dividing plane that still
        allows for the possibility that the voxel is intercepted by the plane.

        Returns:
            The maximum distance a voxel can be from a dividing plane and still
            be intercepted by the plane.
        """
        # We need to find the coordinates that make up a single voxel. This
        # is just the cartesian coordinates of the unit cell divided by
        # its grid size
        end = [0, 0, 0]
        vox_a = [x / self.shape[0] for x in self.a]
        vox_b = [x / self.shape[1] for x in self.b]
        vox_c = [x / self.shape[2] for x in self.c]
        # We want the three other vertices on the other side of the voxel. These
        # can be found by adding the vectors in a cycle (e.g. a+b, b+c, c+a)
        vox_a1 = [x + x1 for x, x1 in zip(vox_a, vox_b)]
        vox_b1 = [x + x1 for x, x1 in zip(vox_b, vox_c)]
        vox_c1 = [x + x1 for x, x1 in zip(vox_c, vox_a)]
        # The final vertex can be found by adding the last unsummed vector to any
        # of these
        end1 = [x + x1 for x, x1 in zip(vox_a1, vox_c)]
        # The center of the voxel sits exactly between the two ends
        center = [(x + x1) / 2 for x, x1 in zip(end, end1)]
        # Shift each point here so that the origin is the center of the
        # voxel.
        voxel_vertices = []
        for vector in [
            center,
            end,
            vox_a,
            vox_b,
            vox_c,
            vox_a1,
            vox_b1,
            vox_c1,
            end,
        ]:
            new_vector = [(x - x1) for x, x1 in zip(vector, center)]
            voxel_vertices.append(new_vector)

        # Now we need to find the maximum distance from the center of the voxel
        # to one of its edges. This should be at one of the vertices.
        # We can't say for sure which one is the largest distance so we find all
        # of their distances and return the maximum
        max_distance = max([np.linalg.norm(vector) for vector in voxel_vertices])
        return max_distance

    @property
    def permutations(self):
        """
        The permutations for translating a voxel coordinate to nearby unit
        cells. This is necessary for the many voxels that will not be directly
        within an atoms partitioning.

        Returns:
            A list of voxel permutations unique to the grid dimensions.
        """
        a, b, c = self.shape
        permutations = [
            (t, u, v)
            for t, u, v in itertools.product([-a, 0, a], [-b, 0, b], [-c, 0, c])
        ]
        # sort permutations. There may be a better way of sorting them. I
        # noticed that generally the correct site was found most commonly
        # for the original site and generally was found at permutations that
        # were either all negative/0 or positive/0
        permutations_sorted = []
        for item in permutations:
            if all(val <= 0 for val in item):
                permutations_sorted.append(item)
            elif all(val >= 0 for val in item):
                permutations_sorted.append(item)
        for item in permutations:
            if item not in permutations_sorted:
                permutations_sorted.append(item)
        permutations_sorted.insert(0, permutations_sorted.pop(7))
        return permutations_sorted

    @property
    def voxel_resolution(self):
        volume = self.structure.volume
        number_of_voxels = self.shape.prod()
        return number_of_voxels / volume

    @cached_property
    def symmetry_data(self):
        return SpacegroupAnalyzer(self.structure).get_symmetry_dataset()

    @property
    def equivalent_atoms(self):
        return self.symmetry_data.equivalent_atoms

    def interpolate_value_at_frac_coords(
        self, frac_coords, method: str = "linear"
    ) -> list[float]:
        coords = self.get_voxel_coords_from_frac_full_array(np.array(frac_coords))
        padded_data = np.pad(self.total, 10, mode="wrap")

        # interpolate grid to find values that lie between voxels. This is done
        # with a cruder interpolation here and then the area close to the minimum
        # is examened more closely with a more rigorous interpolation in
        # get_line_frac_min
        a, b, c = self.get_padded_grid_axes(10)
        fn = RegularGridInterpolator((a, b, c), padded_data, method=method)
        values = []
        for pos in coords:
            adjusted_pos = [x + 10 for x in pos]
            value = float(fn(adjusted_pos))
            values.append(value)
        return values

    def get_2x_supercell(self, data: NDArray):
        """
        Duplicates data with the same dimensions as the grid to make a 2x2x2
        supercell

        Args:
            data (NDArray):
                The data to duplicate. Must have the same dimensions as the
                grid.

        Returns:
            The duplicated data
        """
        raveled_data = data.ravel()
        voxel_indices = np.indices(data.shape).reshape(3, -1).T
        transformations = [
            [0, 0, 0],  # -
            [1, 0, 0],  # x
            [0, 1, 0],  # y
            [0, 0, 1],  # z
            [1, 1, 0],  # xy
            [1, 0, 1],  # xz
            [0, 1, 1],  # yz
            [1, 1, 1],  # xyz
        ]
        transformations = np.array(transformations)
        transformations = self.get_voxel_coords_from_frac(transformations.T).T
        supercell = np.zeros(np.array(data.shape) * 2)
        for transformation in transformations:
            transformed_indices = (voxel_indices + transformation).astype(int)
            x = transformed_indices[:, 0]
            y = transformed_indices[:, 1]
            z = transformed_indices[:, 2]
            supercell[x, y, z] = raveled_data
        return supercell

    def get_voxels_in_radius(self, radius: float, voxel: NDArray):
        """
        Gets the indices of the voxels in a radius around a voxel

        Args:
            radius (float):
                The radius in Angstroms around the voxel

            voxel (NDArray):
                The voxel coordinates of the voxel to find the sphere around

        Returns:
            The voxel indices of the voxels within the provided radius
        """
        voxel = np.array(voxel)
        # Get the distance from each voxel to the origin
        voxel_distances = self.voxel_dist_to_origin

        # Get the indices that are within the radius
        sphere_indices = np.where(voxel_distances <= radius)
        sphere_indices = np.column_stack(sphere_indices)

        # Get indices relative to the voxel
        sphere_indices = sphere_indices + voxel
        # adjust voxels to wrap around grid
        # line = [[round(float(a % b), 12) for a, b in zip(position, grid_data.shape)]]
        new_x = (sphere_indices[:, 0] % self.shape[0]).astype(int)
        new_y = (sphere_indices[:, 1] % self.shape[1]).astype(int)
        new_z = (sphere_indices[:, 2] % self.shape[2]).astype(int)
        sphere_indices = np.column_stack([new_x, new_y, new_z])
        # return new_x, new_y, new_z
        return sphere_indices

    def get_voxels_transformations_to_radius(self, radius: float):
        """
        Gets the transformations required to move from a voxel to the voxels
        surrounding it within the provided radius

        Args:
            radius (float):
                The radius in Angstroms around the voxel

        Returns:
            An array of transformations to add to a voxel to get to each of the
            voxels within the radius surrounding it
        """
        # Get voxels around origin
        voxel_distances = self.voxel_dist_to_origin
        # sphere_grid = np.where(voxel_distances <= radius, True, False)
        # eroded_grid = binary_erosion(sphere_grid)
        # shell_indices = np.where(sphere_grid!=eroded_grid)
        shell_indices = np.where(voxel_distances <= radius)
        # Now we want to translate these indices to next to the corner so that
        # we can use them as transformations to move a voxel to the edge
        final_shell_indices = []
        for a, x in zip(self.shape, shell_indices):
            new_x = x - a
            abs_new_x = np.abs(new_x)
            new_x_filter = abs_new_x < x
            final_x = np.where(new_x_filter, new_x, x)
            final_shell_indices.append(final_x)

        return np.column_stack(final_shell_indices)

    def get_padded_grid_axes(self, padding: int = 0):
        """
        Gets the the possible indices for each dimension of a padded grid.
        e.g. if the original charge density grid is 20x20x20, and is padded
        with one extra layer on each side, this function will return three
        arrays with integers from 0 to 21.

        Args:
            padding (int):
                The amount the grid has been padded

        Returns:
            three arrays with lengths the same as the grids shape
        """
        grid = self.total
        a = np.linspace(
            0,
            grid.shape[0] + (padding - 1) * 2 + 1,
            grid.shape[0] + padding * 2,
        )
        b = np.linspace(
            0,
            grid.shape[1] + (padding - 1) * 2 + 1,
            grid.shape[1] + padding * 2,
        )
        c = np.linspace(
            0,
            grid.shape[2] + (padding - 1) * 2 + 1,
            grid.shape[2] + padding * 2,
        )
        return a, b, c

    def copy(self):
        """
        Convenience method to get a copy of the grid.

        Returns:
            A copy of the Grid.
        """
        return self.__class__(
            self.structure.copy(),
            self.data.copy(),
        )

    @classmethod
    def from_file(cls, grid_file: str | Path):
        """Create a grid instance using a CHGCAR or ELFCAR file

        Args:
            grid_file (string):
                The file the instance should be made from. Should be a VASP
                CHGCAR or ELFCAR type file.

        Returns:
            Grid from the specified file.
        """
        logging.info(f"Loading {grid_file} from file")
        # Create string to add structure to.
        poscar, data, _ = cls.parse_file(grid_file)

        return Grid(poscar.structure, data)

    def to_pybader(self):
        """
        Returns a Bader object from pybader.
        """
        # make sure the pybader package is present
        try:
            from pybader.interface import Bader
        except:
            raise Exception(
                "This method requires the pybader module."
                "Install this with `conda install -c conda-forge pybader`"
            )
        atoms = self.structure.cart_coords
        lattice = self.matrix
        density = {"charge": self.total}
        file_info = {"voxel_offset": np.array([0, 0, 0])}
        bader = Bader(density, lattice, atoms, file_info)
        return bader

    def run_pybader(self, threads: int = 1):
        """
        Convenience class for running zero-flux voxel assignment using pybader.
        Returns a pybader Bader class object with the assigned voxels

        Args:
            cores (int):
                The number of threads to use when running the Bader algorithm
        """
        logging.info("Running Bader")
        bader = self.to_pybader()
        bader.load_config("speed")
        bader.threads = threads
        bader.spin_flag = True  # loading speed config resets all config vars
        bader.volumes_init()
        bader.bader_calc()
        bader.bader_to_atom_distance()
        bader.refine_volumes(bader.atoms_volumes)
        bader.threads = 1
        bader.min_surface_distance()
        return bader

    def regrid(
        self,
        desired_resolution: int = 130000,
        new_shape: np.array = None,
        order: int = 3,
    ):
        """
        Returns a new grid resized using scipy's ndimage.zoom method

        Args:
            desired_resolution (int):
                The desired resolution in voxels/A^3.
            new_shape (NDArray):
                The new array shape. Takes precedence over desired_resolution.
            order (int):
                The order of spline interpolation to use.

        Returns:
            Changes the grid data in place.
        """
        # Get data
        total = self.total
        diff = self.diff

        # # Get the lattice unit vectors as a 3x3 array
        # lattice_array = self.matrix

        # get the original grid size and lattice volume.
        shape = self.shape
        volume = self.structure.volume

        if new_shape is None:
            # calculate how much the number of voxels along each unit cell must be
            # multiplied to reach the desired resolution.
            scale_factor = ((desired_resolution * volume) / shape.prod()) ** (1 / 3)

            # calculate the new grid shape. round up to the nearest integer for each
            # side
            new_shape = np.around(shape * scale_factor).astype(np.int32)

        # get the factor to zoom by
        zoom_factor = new_shape / shape
        # get the new total data
        new_total = zoom(
            total, zoom_factor, order=order, mode="grid-wrap", grid_mode=True
        )  # , prefilter=False,)
        # if the diff exists, get the new diff data
        if diff is not None:
            new_diff = zoom(
                diff, zoom_factor, order=order, mode="grid-wrap", grid_mode=True
            )  # , prefilter=False,)

        # get the new data dict and return a new grid
        data = {"total": new_total, "diff": new_diff}

        return Grid(self.structure, data)

    def split_to_spin(self, data_type: Literal["elf", "charge"] = "elf"):
        """
        Splits the grid to spin up and spin down contributions
        """
        # first check if the grid has spin parts
        if not self.is_spin_polarized:
            raise Exception(
                "Only one set of data detected. The grid cannot be split into spin up and spin down"
            )
        # Now we get the separate data parts. If the data is ELF, the parts are
        # stored as total=spin up and diff = spin down
        if data_type == "elf":
            spin_up_data = self.total.copy()
            spin_down_data = self.diff.copy()
        elif data_type == "charge":
            spin_data = self.spin_data
            # pymatgen uses some custom class as keys here
            for key in spin_data.keys():
                if key.value == 1:
                    spin_up_data = spin_data[key].copy()
                elif key.value == -1:
                    spin_down_data = spin_data[key].copy()

        # convert to dicts
        spin_up_data = {"total": spin_up_data}
        spin_down_data = {"total": spin_down_data}

        spin_up_grid = self.__class__(
            self.structure.copy(),
            spin_up_data,
        )
        spin_down_grid = self.__class__(
            self.structure.copy(),
            spin_down_data,
        )

        return spin_up_grid, spin_down_grid

    @classmethod
    def sum_grids(cls, grid1, grid2):
        """
        Takes in two grids and returns a single grid summing their values.

        Args:
            grid1 (Grid):
                The first grid to sum

            grid2 (Grid):
                The second grid to sum

        Returns:
            A Grid object with both the total and diff parts summed

        """
        if not np.all(grid1.shape == grid2.shape):
            logging.exception("Grids must have the same size.")
        total1 = grid1.total
        diff1 = grid1.diff

        total2 = grid2.total
        diff2 = grid2.diff

        total = total1 + total2
        if diff1 is not None and diff2 is not None:
            diff = diff1 + diff2
            data = {"total": total, "diff": diff}
        else:
            data = {"total": total, "diff": None}

        # Note that we copy the first grid here rather than making a new grid
        # instance because we want to keep any useful information such as whether
        # the grid is spin polarized or not.
        new_grid = grid1.copy()
        new_grid.data = data
        return new_grid

    @staticmethod
    def label(input: NDArray, structure: NDArray = np.ones([3, 3, 3])):
        """
        Uses scipy's ndimage package to label an array, and corrects for
        periodic boundaries
        """
        if structure is not None:
            labeled_array, _ = label(input, structure)
            # Features connected through opposite sides of the unit cell should
            # have the same label, but they don't currently. To handle this, we
            # pad our featured grid, re-label it, and check if the new labels
            # contain multiple of our previous labels.
            padded_featured_grid = np.pad(labeled_array, 1, "wrap")
            relabeled_array, label_num = label(padded_featured_grid, structure)
        else:
            labeled_array, _ = label(input)
            padded_featured_grid = np.pad(labeled_array, 1, "wrap")
            relabeled_array, label_num = label(padded_featured_grid)

        connections = UnionFind()
        for i in range(label_num):
            mask = relabeled_array == i
            connected_features = np.unique(padded_featured_grid[mask])
            for feature in connected_features[1:]:
                connections.union(connected_features[0], feature)
        # Get the sets of basins that are connected to each other
        connection_sets = list(connections.to_sets())
        for label_set in connection_sets:
            label_set = np.array(list(label_set))
            # replace all of these labels with the lowest one
            labeled_array = np.where(
                np.isin(labeled_array, label_set),
                label_set[0],
                labeled_array,
            )
        # Now we reduce the feature labels so that they start at 0
        for i, j in enumerate(np.unique(labeled_array)):
            labeled_array = np.where(labeled_array == j, i, labeled_array)

        return labeled_array

    @staticmethod
    def periodic_center_of_mass(labels, label_vals=None) -> NDArray:
        """
        Computes center of mass for each label in a 3D periodic array.

        Args:
            labels: 3D array of integer labels
            label_vals: list/array of unique labels to compute (default: all nonzero)

        Returns:
            A 3xN array of centers of mass
        """
        shape = labels.shape
        if label_vals is None:
            label_vals = np.unique(labels)
            label_vals = label_vals[label_vals != 0]

        centers = []
        for val in label_vals:
            # get the voxel coords for each voxel in this label
            coords = np.array(np.where(labels == val)).T  # shape (N, 3)
            # If we have no coords for this label, we skip
            if coords.shape[0] == 0:
                continue

            # From chap-gpt: Get center of mass using spherical distance
            center = []
            for i, size in enumerate(shape):
                angles = coords[:, i] * 2 * np.pi / size
                x = np.cos(angles).mean()
                y = np.sin(angles).mean()
                mean_angle = np.arctan2(y, x)
                mean_pos = (mean_angle % (2 * np.pi)) * size / (2 * np.pi)
                center.append(mean_pos)
            centers.append(center)
        centers = np.array(centers)
        centers = centers.round(6)

        return centers

    def get_critical_points(
        self, array: NDArray, threshold: float = 5e-03, return_hessian_s: bool = True
    ):
        """
        Finds the critical points in the grid. If return_hessians is true,
        the hessian matrices for each critical point will be returned along
        with their type index.
        """
        # !!! Check if padding and threshold effect final result
        # get gradient using a padded grid to handle periodicity
        padding = 2
        a, b, c = self.get_padded_grid_axes(padding)
        padded_array = np.pad(array, padding, mode="wrap")
        dx, dy, dz = np.gradient(padded_array)

        # get magnitude of the gradient
        magnitude = np.sqrt(dx**2 + dy**2 + dz**2)

        # unpad the magnitude
        slicer = tuple(slice(padding, -padding) for _ in range(3))
        magnitude = magnitude[slicer]

        # now we want to get where the magnitude is close to 0. To do this, we
        # will create a mask where the magnitude is below a threshold. We will
        # then label the regions where this is true using scipy, then combine
        # the regions into one
        magnitude_mask = magnitude < threshold
        # critical_points = np.where(magnitude<threshold)
        # padded_critical_points = np.array(critical_points).T + padding

        label_structure = np.ones((3, 3, 3), dtype=int)
        labeled_magnitude_mask = self.label(magnitude_mask, label_structure)
        min_indices = []
        for idx in np.unique(labeled_magnitude_mask):
            label_mask = labeled_magnitude_mask == idx
            label_indices = np.where(label_mask)
            min_mag = magnitude[label_indices].min()
            min_indices.append(np.argwhere((magnitude == min_mag) & label_mask)[0])
        min_indices = np.array(min_indices)

        critical_points = min_indices[:, 0], min_indices[:, 1], min_indices[:, 2]

        # critical_points = self.periodic_center_of_mass(labeled_magnitude_mask)
        padded_critical_points = tuple([i + padding for i in critical_points])
        values = array[critical_points]
        # # get the value at each of these critical points
        # fn_values = RegularGridInterpolator((a, b, c), padded_array , method="linear")
        # values = fn_values(padded_critical_points)

        if not return_hessian_s:
            return critical_points, values

        # now we want to get the hessian eigenvalues around each of these points
        # using interpolation. First, we get the second derivatives
        d2f_dx2 = np.gradient(dx, axis=0)
        d2f_dy2 = np.gradient(dy, axis=1)
        d2f_dz2 = np.gradient(dz, axis=2)
        # # now create interpolation functions for each
        # fn_dx2 = RegularGridInterpolator((a, b, c), d2f_dx2, method="linear")
        # fn_dy2 = RegularGridInterpolator((a, b, c), d2f_dy2, method="linear")
        # fn_dz2 = RegularGridInterpolator((a, b, c), d2f_dz2, method="linear")
        # and calculate the hessian eigenvalues for each point
        # H00 = fn_dx2(padded_critical_points)
        # H11 = fn_dy2(padded_critical_points)
        # H22 = fn_dz2(padded_critical_points)
        H00 = d2f_dx2[padded_critical_points]
        H11 = d2f_dy2[padded_critical_points]
        H22 = d2f_dz2[padded_critical_points]
        # summarize the hessian eigenvalues by getting the sum of their signs
        hessian_eigs = np.array([H00, H11, H22])
        hessian_eigs = np.moveaxis(hessian_eigs, 1, 0)
        hessian_eigs_signs = np.where(hessian_eigs > 0, 1, hessian_eigs)
        hessian_eigs_signs = np.where(hessian_eigs < 0, -1, hessian_eigs_signs)
        # Now we get the sum of signs for each set of hessian eigenvalues
        s = np.sum(hessian_eigs_signs, axis=1)

        return critical_points, values, s

    ###########################################################################
    # The following is a series of methods that are useful for converting between
    # voxel coordinates, fractional coordinates, and cartesian coordinates.
    # Voxel coordinates go from 0 to grid_size-1. Fractional coordinates go
    # from 0 to 1. Cartesian coordinates convert to real space based on the
    # crystal lattice.
    ###########################################################################
    def get_voxel_coords_from_index(self, site):
        """
        Takes in a site index and returns the equivalent voxel grid index.

        Args:
            site (int):
                the index of the site to find the grid index for

        Returns:
            A voxel grid index as an array.

        """

        voxel_coords = [a * b for a, b in zip(self.shape, self.frac_coords[site])]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_neigh_CrystalNN(self, neigh):
        """
        Gets the voxel grid index from a neighbor atom object from CrystalNN or
        VoronoiNN

        Args:
            neigh (Neigh):
                a neighbor type object from pymatgen

        Returns:
            A voxel grid index as an array.
        """
        grid_size = self.shape
        frac = neigh["site"].frac_coords
        voxel_coords = [a * b for a, b in zip(grid_size, frac)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_neigh(self, neigh):
        """
        Gets the voxel grid index from a neighbor atom object from the pymatgen
        structure.get_neighbors class.

        Args:
            neigh (dict):
                a neighbor dictionary from pymatgens structure.get_neighbors
                method.

        Returns:
            A voxel grid index as an array.
        """
        grid_size = self.shape
        frac_coords = neigh.frac_coords
        voxel_coords = [a * b for a, b in zip(grid_size, frac_coords)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_frac(self, frac_coords: NDArray | list):
        """
        Takes in a fractional coordinate and returns the cartesian coordinate.

        Args:
            frac_coords (NDArray):
                The fractional position to convert to cartesian coords.

        Returns:
            A voxel grid index as an array.

        """
        grid_size = self.shape
        voxel_coords = [a * b for a, b in zip(grid_size, frac_coords)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_frac_coords_from_vox(self, voxel_coords: NDArray | list):
        """
        Takes in a voxel grid index and returns the fractional
        coordinates.

        Args:
            voxel_coords (NDArray):
                A voxel grid index

        Returns:
            A fractional coordinate as an array
        """
        size = self.shape
        fa, fb, fc = [(a / b) for a, b in zip(voxel_coords, size)]
        frac_coords = np.array([fa, fb, fc])
        return frac_coords

    def get_cart_coords_from_frac(self, frac_coords: NDArray | list):
        """
        Takes in fractional coordinates and returns cartesian coordinates

        Args:
            frac_coords (NDArray):
                The fractional position to convert to cartesian coords.

        Returns:
            Cartesian coordinates as an array
        """
        fa, fb, fc = frac_coords[0], frac_coords[1], frac_coords[2]
        a, b, c = self.a, self.b, self.c
        x = fa * a[0] + fb * b[0] + fc * c[0]
        y = fa * a[1] + fb * b[1] + fc * c[1]
        z = fa * a[2] + fb * b[2] + fc * c[2]
        cart_coords = np.array([x, y, z])
        return cart_coords

    def get_frac_coords_from_cart(self, cart_coords: NDArray | list):
        """
        Takes in a cartesian coordinate and returns the fractional coordinates.

        Args:
            cart_coords (NDArray):
                A cartesian coordinate.

        Returns:
            fractional coordinates as an Array
        """
        lattice_matrix = self.matrix
        inverse_matrix = np.linalg.inv(lattice_matrix)
        frac_coords = np.dot(cart_coords, inverse_matrix)

        return frac_coords

    def get_cart_coords_from_vox(self, voxel_coords: NDArray | list):
        """
        Takes in a voxel grid index and returns the cartesian coordinates.

        Args:
            voxel_coords (NDArray):
                A voxel grid index

        Returns:
            Cartesian coordinates as an array
        """
        frac_coords = self.get_frac_coords_from_vox(voxel_coords)
        cart_coords = self.get_cart_coords_from_frac(frac_coords)
        return cart_coords

    def get_voxel_coords_from_cart(self, cart_coords: NDArray | list):
        """
        Takes in a cartesian coordinate and returns the voxel coordinates.

        Args:
            cart_coords (NDArray): A cartesian coordinate.

        Returns:
            Voxel coordinates as an Array
        """
        frac_coords = self.get_frac_coords_from_cart(cart_coords)
        voxel_coords = self.get_voxel_coords_from_frac(frac_coords)
        return voxel_coords

    def get_cart_coords_from_frac_full_array(self, frac_coords: NDArray):
        """
        Takes in a 2D array of shape (N,3) representing fractional coordinates
        at N points and calculates the equivalent cartesian coordinates.

        Args:
            frac_coords (NDArray):
                An (N,3) shaped array of fractional coordinates

        Returns:
            An (N,3) shaped array of cartesian coordinates
        """
        x, y, z = self.matrix.T
        cart_x = np.dot(frac_coords, x)
        cart_y = np.dot(frac_coords, y)
        cart_z = np.dot(frac_coords, z)
        cart_coords = np.column_stack([cart_x, cart_y, cart_z])
        return cart_coords

    def get_frac_coords_from_vox_full_array(self, vox_coords: NDArray):
        """
        Takes in a 2D array of shape (N,3) representing voxel coordinates
        at N points and calculates the equivalent fractional coordinates.

        Args:
            vox_coords (NDArray):
                An (N,3) shaped array of voxel coordinates

        Returns:
            An (N,3) shaped array of fractional coordinates
        """
        x, y, z = self.shape
        frac_x = vox_coords[:, 0] / x
        frac_y = vox_coords[:, 1] / y
        frac_z = vox_coords[:, 2] / z
        frac_coords = np.column_stack([frac_x, frac_y, frac_z])
        return frac_coords

    def get_voxel_coords_from_frac_full_array(self, frac_coords: NDArray):
        """
        Takes in a 2D array of shape (N,3) representing fractional coordinates
        at N points and calculates the equivalent voxel coordinates.

        Args:
            frac_coords (NDArray):
                An (N,3) shaped array of fractional coordinates

        Returns:
            An (N,3) shaped array of voxel coordinates
        """
        x, y, z = self.shape
        vox_x = frac_coords[:, 0] * x
        vox_y = frac_coords[:, 1] * y
        vox_z = frac_coords[:, 2] * z
        vox_coords = np.column_stack([vox_x, vox_y, vox_z])
        return vox_coords

    def get_cart_coords_from_vox_full_array(self, vox_coords: NDArray):
        """
        Takes in a 2D array of shape (N,3) representing voxel coordinates
        at N points and calculates the equivalent cartesian coordinates.

        Args:
            frac_coords (NDArray):
                An (N,3) shaped array of voxel coordinates

        Returns:
            An (N,3) shaped array of cartesian coordinates
        """
        frac_coords = self.get_frac_coords_from_vox_full_array(vox_coords)
        return self.get_cart_coords_from_frac_full_array(frac_coords)

    def _plot_points(self, points, ax, fig, color, size: int = 20):
        """
        Plots points of form [x,y,z] using matplotlib

        Args:
            points (list): A list of points to plot
            fig: A matplotlib.pyplot.figure() instance
            ax: A matplotlib Subplot instance
            color (str): The color to plot the points
            size (int): The pt size to plot
        """
        x = []
        y = []
        z = []
        for point in points:
            x.append(point[0])
            y.append(point[1])
            z.append(point[2])
        ax.scatter(x, y, z, c=color, s=size)

    def _plot_unit_cell(self, ax, fig):
        """
        Plots the unit cell of a structure using matplotlib

        Args:
            fig: A matplotlib.pyplot.figure() instance
            ax: A matplotlib Subplot instance
        """
        if ax is None or fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d")

        # Get the points at the lattice vertices to plot and plot them
        a = self.a
        b = self.b
        c = self.c
        points = [np.array([0, 0, 0]), a, b, c, a + b, a + c, b + c, a + b + c]
        self._plot_points(points, ax, fig, "purple")

        # get the structure to plot.
        structure = self.structure
        species = structure.symbol_set

        # get a color map to distinguish between sites
        color_map = matplotlib.colormaps.get_cmap("tab10")
        # Go through each atom type and plot all instances with the same color
        for i, specie in enumerate(species):
            color = color_map(i)
            sites_indices = structure.indices_from_symbol(specie)
            for site in sites_indices:
                coords = structure[site].coords
                self._plot_points([coords], ax, fig, color, size=40)
