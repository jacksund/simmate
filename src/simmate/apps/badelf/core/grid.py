# -*- coding: utf-8 -*-

import itertools
import logging
import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import ArrayLike
from pymatgen.io.vasp import Poscar
from pyrho.pgrid import PGrid

from simmate.toolkit import Structure


class Grid:
    """
    A grid object. Contains information from a VASP CHGCAR or ELFCAR type file.
    This class is used heavily during

    Args:
        total (ArrayLike): A 3D array of values corresponding to the total
            charge density of a CHGCAR type file or the spin up portion of an
            ELFCAR file.
        diff: (ArrayLike): A 3D array of values corresponding to the
            magnetization density of a CHGCAR type file or the spin down portion
            of an ELFCAR file.
        structure (Structure): a pymatgen Structure type object.
        data_type (str): The type of data, either "elf" or "charge density"
    """

    def __init__(
        self,
        total: ArrayLike,
        diff: ArrayLike | None,
        structure: Structure,
        data_type: str,
    ):
        if diff is not None and diff.shape != total.shape:
            raise ValueError("total and diff arrays must have the same shape.")
        self.total = total
        self.diff = diff
        self.structure = structure
        if data_type not in ["elf", "charge density", "unknown"]:
            raise ValueError("data type must be 'elf', 'charge density', or 'unknown'")
        self.data_type = data_type

    @property
    def grid_shape(self):
        """Data grid shape

        Returns:
            The number of voxels along each unit cell vector
        """
        return np.array(self.total.shape)

    @property
    def a(self):
        """The cartesian coordinates for the lattice vector "a"

        Returns:
            The cartesian coordinates for the lattice vector "a"
        """
        return self.structure.lattice.matrix[0]

    @property
    def b(self):
        """The cartesian coordinates for the lattice vector "b"

        Returns:
            The cartesian coordinates for the lattice vector "b"
        """
        return self.structure.lattice.matrix[1]

    @property
    def c(self):
        """The cartesian coordinates for the lattice vector "c"

        Returns:
            The cartesian coordinates for the lattice vector "c"
        """
        return self.structure.lattice.matrix[2]

    @property
    def frac_coords(self):
        """The fractional coordinates of every atom in the structure

        Returns:
            Array of coordinates for each atom.
        """
        return self.structure.frac_coords

    @property
    def voxel_volume(self):
        """The volume of each voxel in the grid

        Returns:
            The volume of a voxel
        """
        volume = self.structure.volume
        voxel_num = np.prod(self.grid_shape)
        return volume / voxel_num

    @property
    def voxel_num(self):
        return self.grid_shape.prod()

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
        vox_a = [x / self.grid_shape[0] for x in self.a]
        vox_b = [x / self.grid_shape[1] for x in self.b]
        vox_c = [x / self.grid_shape[2] for x in self.c]
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
        for vector in [center, end, vox_a, vox_b, vox_c, vox_a1, vox_b1, vox_c1, end]:
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
        a, b, c = self.grid_shape
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
        number_of_voxels = self.grid_shape.prod()
        return number_of_voxels / volume

    def get_grid_axes(self, padding: int = 0):
        """
        Gets the the possible indices for each dimension of a padded grid.
        e.g. if the original charge density grid is 20x20x20, and is padded
        with one extra layer on each side, this function will return three
        arrays with integers from 0 to 21.

        Args:
            padding (int): The amount the grid has been padded

        Returns:
            three arrays with lengths the same as the grids shape
        """
        grid = self.total
        a = np.linspace(
            0, grid.shape[0] + (padding - 1) * 2 + 1, grid.shape[0] + padding * 2
        )
        b = np.linspace(
            0, grid.shape[1] + (padding - 1) * 2 + 1, grid.shape[1] + padding * 2
        )
        c = np.linspace(
            0, grid.shape[2] + (padding - 1) * 2 + 1, grid.shape[2] + padding * 2
        )
        return a, b, c

    def copy(self):
        """
        Convenience method to get a copy of the grid.

        Returns:
            A copy of the Grid.
        """
        return self.__class__(
            self.total,
            self.diff,
            self.structure.copy(),
            self.data_type,
        )

    @classmethod
    def from_file(cls, grid_file: str | Path):
        """Create a grid instance using a CHGCAR or ELFCAR file

        Args:
            grid_file (string): The file the instance should be made from. Should
                be a VASP CHGCAR or ELFCAR type file.

        Returns:
            Grid from the specified file.
        """
        logging.info(f"Loading {grid_file} from file")
        # Create string to add structure to.
        structure_str = ""
        total_str = ""
        diff_str = ""

        # Read the content of the file. We will need the number of atoms and the
        # grid shape to read in the data.
        with open(grid_file) as f:
            content = f.readlines()

            # get the number of atoms in the structure
            num_atoms = sum([int(x) for x in content[6].split()])
            # get the grid shape of the data
            grid_shape_str = content[9 + num_atoms]
            grid_shape = [int(x) for x in grid_shape_str.split()]
            # get the first row of data. This will be used to determine the
            # format of the file.
            first_data_row = content[10 + num_atoms]

            # Get the structure as a string
            for line in content[0 : 8 + num_atoms]:
                structure_str += f"{line}"

            # The format that VASP outputs for CHGCARs and ELFCARs can have several
            # different forms. The data is effectively a long list of values going
            # in order of array indices.
            # Typically the CHGCAR will have 5 values per line while the
            # ELFCAR will have 10 if they are directly from a VASP calculation.
            # If they are outputted from pymatgen or this grid class they will both
            # have 5 columns. This will effect the number of lines of data there are.
            column_num = len(first_data_row.split())
            line_num = math.ceil(np.product(grid_shape) / column_num)
            skip_rows_total = 10 + num_atoms

            # Get the total grid as a string.
            for line in content[skip_rows_total : skip_rows_total + line_num]:
                total_str += f"{line}"

            # charge density file have a set of augmentation occupancies stored
            # after the charge density. We can look for a line containing this
            # to determine the data type. We also need to determine how many
            # lines this data takes up.
            aug_occ_lines_num = 0
            try:
                if "augmentation occupancies" in content[skip_rows_total + line_num]:
                    data_type = "charge density"
                    for line in content[skip_rows_total + line_num :]:
                        # If we find the start of a new set of data or the end of
                        # the file we end.
                        if grid_shape_str in line:
                            break
                        else:
                            aug_occ_lines_num += 1

                else:
                    data_type = "elf"

                # If the VASP calculation was spin polarized there will be another
                # set of data. We check this is true and then read in the data if
                # it exists
                skip_rows_diff = skip_rows_total + line_num + aug_occ_lines_num + 1
                if grid_shape_str in content[skip_rows_diff - 1]:
                    # there is a second set of data we need to load
                    for line in content[skip_rows_diff : skip_rows_diff + line_num]:
                        diff_str += f"{line}"
            except:
                # We've reached the end of the file without finding an
                # augmentation occupancies or additional set of data. We either
                # have a non-spin polarized ELF file or the output
                # BvAt_.dat file from the Henkelman Bader code.
                data_type = "unknown"

        # Create the structure object
        structure = Structure.from_str(structure_str, fmt="poscar")

        # Load in the data for the first set of data (spin up in ELFCAR, total
        # charge density in CHGCAR). Ravel moves the data from the original
        # grid in the file to a long list. Reshape moves it into a 3D numpy array
        # with the appropriate shape.
        total = (
            np.fromstring(
                total_str,
                sep=" ",
            )
            .ravel()
            .reshape(grid_shape, order="F")
        )

        # Do the same for the second set of data (spin down in ELFCAR, magnetic
        # moment in CHGCAR)
        if len(diff_str) > 0:
            diff = (
                np.fromstring(
                    diff_str,
                    sep=" ",
                )
                .ravel()
                .reshape(grid_shape, order="F")
            )
        else:
            diff = None

        return Grid(total, diff, structure, data_type)

    def write_file(self, file_name: str | Path, vasp4_compatible=False):
        """
        Writes a vasp compatible file. This is a reimplimentation of pymatgen's
        [version](https://github.com/materialsproject/pymatgen/blob/v2023.10.4/pymatgen/io/vasp/outputs.py) without the required overhead.
        Args:
            file_name (str | Path): Path to file
            vasp4_compatible: True if the format is vasp4 compatible.
        """
        logging.info(f"Writing to {file_name}")

        def _print_fortran_float(flt):
            """Fortran codes print floats with a leading zero in scientific
            notation. When writing CHGCAR files, we adopt this convention
            to ensure written CHGCAR files are byte-to-byte identical to
            their input files as far as possible.

            Args:
                flt (float): Float to print.

            Returns:
                str: String representation of float in Fortran format.
            """
            s = f"{flt:.10E}"
            if flt >= 0:
                return f"0.{s[0]}{s[2:12]}E{int(s[13:]) + 1:+03}"
            return f"-.{s[1]}{s[3:13]}E{int(s[14:]) + 1:+03}"

        with open(file_name, "wt") as file:
            poscar = Poscar(self.structure)

            # use original name if it's been set (e.g. from Chgcar)
            comment = getattr(self, "name", poscar.comment)

            lines = comment + "\n"
            lines += "   1.00000000000000\n"
            for vec in self.structure.lattice.matrix:
                lines += f" {vec[0]:12.6f}{vec[1]:12.6f}{vec[2]:12.6f}\n"
            if not vasp4_compatible:
                lines += "".join(f"{s:5}" for s in poscar.site_symbols) + "\n"
            lines += "".join(f"{x:6}" for x in poscar.natoms) + "\n"
            lines += "Direct\n"
            for site in self.structure:
                dim, b, c = site.frac_coords
                lines += f"{dim:10.6f}{b:10.6f}{c:10.6f}\n"
            lines += " \n"
            file.write(lines)
            dim = self.grid_shape

            def write_spin(data):
                lines = []
                count = 0
                file.write(f"   {dim[0]}   {dim[1]}   {dim[2]}\n")
                for k, j, i in itertools.product(
                    list(range(dim[2])), list(range(dim[1])), list(range(dim[0]))
                ):
                    lines.append(_print_fortran_float(data[i, j, k]))
                    count += 1
                    if count % 5 == 0:
                        file.write(" " + "".join(lines) + "\n")
                        lines = []
                    else:
                        lines.append(" ")
                if count % 5 != 0:
                    file.write(" " + "".join(lines) + " \n")

            write_spin(self.total)
            if self.diff is not None:
                write_spin(self.diff)

    def regrid(
        self,
        desired_resolution: int = 130000,
        new_grid_shape: np.array = None,
    ):
        """
        Resizes the grid using Fourier interplation as implemented by
        [PyRho](https://materialsproject.github.io/pyrho/)

        Args:
            desired_resolution (int): The desired resolution in voxels/A^3.
            new_grid_shape (ArrayLike): The new array shape. Takes precedence
                over desired_resolution.

        Returns:
            Changes the grid data in place.
        """
        # Get data
        total = self.total
        diff = self.diff

        # Get the lattice unit vectors as a 3x3 array
        lattice_array = self.structure.lattice.matrix

        # get the original grid size and lattice volume.
        grid_shape = self.grid_shape
        volume = self.structure.volume

        if new_grid_shape is None:
            # calculate how much the number of voxels along each unit cell must be
            # multiplied to reach the desired resolution.
            scale_factor = ((desired_resolution * volume) / grid_shape.prod()) ** (
                1 / 3
            )

            # calculate the new grid shape. round up to the nearest integer for each
            # side
            new_grid_shape = np.around(grid_shape * scale_factor).astype(np.int32)

        # create a pyrho pgrid instance.
        total_pgrid = PGrid(total, lattice_array)

        # regrid to the desired voxel resolution and get the data back out.
        new_total_pgrid = total_pgrid.get_transformed(
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]], new_grid_shape
        )
        # new_data = pgrid.lossy_smooth_compression(new_grid_shape)
        new_total_data = new_total_pgrid.grid_data
        # update class total instance
        self.total = new_total_data

        # repeat for diff if exists
        if diff is not None:
            diff_pgrid = PGrid(diff, lattice_array)
            new_diff_pgrid = diff_pgrid.get_transformed(
                [[1, 0, 0], [0, 1, 0], [0, 0, 1]], new_grid_shape
            )
            new_diff_data = new_diff_pgrid.grid_data
            self.diff = new_diff_data

    ###########################################################################
    # The following is a series of methods that are useful for converting between
    # voxel coordinates, fractional coordinates, and cartesian coordinates.
    ###########################################################################
    def get_voxel_coords_from_index(self, site):
        """
        Takes in a site index and returns the equivalent voxel grid index.

        Args:
            site (int): the index of the site to find the grid index for

        Returns:
            A voxel grid index as an array.

        """

        voxel_coords = [
            a * b + 1 for a, b in zip(self.grid_shape, self.frac_coords[site])
        ]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_neigh_CrystalNN(self, neigh):
        """
        Gets the voxel grid index from a neighbor atom object from CrystalNN or
        VoronoiNN

        Args:
            neigh (Neigh): a neighbor type object from pymatgen

        Returns:
            A voxel grid index as an array.
        """
        grid_size = self.grid_shape
        frac = neigh["site"].frac_coords
        voxel_coords = [a * b + 1 for a, b in zip(grid_size, frac)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_neigh(self, neigh):
        """
        Gets the voxel grid index from a neighbor atom object from the pymatgen
        structure.get_neighbors class.

        Args:
            neigh (dict): a neighbor dictionary from pymatgens structure.get_neighbors
                method.

        Returns:
            A voxel grid index as an array.
        """
        grid_size = self.grid_shape
        frac_coords = neigh.frac_coords
        voxel_coords = [a * b + 1 for a, b in zip(grid_size, frac_coords)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_voxel_coords_from_frac(self, frac_coords: ArrayLike | list):
        """
        Takes in a fractional coordinate and returns the cartesian coordinate.

        Args:
            frac_coords (ArrayLike): The fractional position to convert to cartesian coords.

        Returns:
            A voxel grid index as an array.

        """
        grid_size = self.grid_shape
        voxel_coords = [a * b + 1 for a, b in zip(grid_size, frac_coords)]
        # voxel positions go from 1 to (grid_size + 0.9999)
        return np.array(voxel_coords)

    def get_frac_coords_from_vox(self, voxel_coordsition: ArrayLike | list):
        """
        Takes in a voxel grid index and returns the fractional
        coordinates.

        Args:
            voxel_coordsition (ArrayLike): A voxel grid index

        Returns:
            A fractional coordinate as an array
        """
        size = self.grid_shape
        fa, fb, fc = [((a - 1) / b) for a, b in zip(voxel_coordsition, size)]
        frac_coords = np.array([fa, fb, fc])
        return frac_coords

    def get_cart_coords_from_frac(self, frac_coords: ArrayLike | list):
        """
        Takes in fractional coordinates and returns cartesian coordinates

        Args:
            frac_coords (ArrayLike): The fractional position to convert to cartesian coords.

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

    def get_frac_coords_from_cart(self, cart_coords: ArrayLike | list):
        """
        Takes in a cartesian coordinate and returns the fractional coordinates.

        Args:
            cart_coords (ArrayLike): A cartesian coordinate.

        Returns:
            fractional coordinates as an Array
        """
        lattice_matrix = self.structure.lattice.matrix
        inverse_matrix = np.linalg.inv(lattice_matrix)
        frac_coords = np.dot(cart_coords, inverse_matrix)

        return frac_coords

    def get_cart_coords_from_vox(self, voxel_coord: ArrayLike | list):
        """
        Takes in a voxel grid index and returns the cartesian coordinates.

        Args:
            voxel_coords (ArrayLike): A voxel grid index

        Returns:
            Cartesian coordinates as an array
        """
        frac_coords = self.get_frac_coords_from_vox(voxel_coord)
        cart_coords = self.get_cart_coords_from_frac(frac_coords)
        return cart_coords

    def get_voxel_coords_from_cart(self, cart_coords: ArrayLike | list):
        """
        Takes in a cartesian coordinate and returns the voxel coordinates.

        Args:
            cart_coords (ArrayLike): A cartesian coordinate.

        Returns:
            Voxel coordinates as an Array
        """
        frac_coords = self.get_frac_coords_from_cart(cart_coords)
        voxel_coords = self.get_voxel_coords_from_frac(frac_coords)
        return voxel_coords

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
