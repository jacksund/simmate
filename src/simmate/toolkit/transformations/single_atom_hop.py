# -*- coding: utf-8 -*-

import random
from copy import deepcopy

import pandas

from simmate.toolkit import Structure
from simmate.toolkit.transformations.base import Transformation


class AtomHop(Transformation):
    """
    Moves a randomly selected atom by a distance up to a maximum value.
    This will typically be about 0.2 A for the RMC process.
    """

    io_scale = "one_to_one"
    ninput = 1
    allow_parallel = False

    @staticmethod
    def apply_transformation(
        structure: Structure,
        max_step=0.2,
        max_attempts=100,
    ):

        """We define a cubic grid, then discard the points outside radius r"""
        """ JACK:  can we cache this so we don't have to repeatedly generate
        the grid??"""

        sphere = []
        divisions = 21
        shift = -max_step
        scale = 2 * max_step

        for i in range(divisions):
            for j in range(divisions):
                for k in range(divisions):
                    x = ((i / (divisions - 1)) * scale) + shift
                    y = ((j / (divisions - 1)) * scale) + shift
                    z = ((k / (divisions - 1)) * scale) + shift
                    distance = (x**2 + y**2 + z**2) ** 0.5
                    if distance < max_step:
                        sphere.append([x, y, z])

        # randomly select an atom and move_vector from this grid

        move_index = random.randrange(structure.composition.num_atoms)
        move_vector = random.sample(sphere, 1)[0]

        print(move_vector)

        old_position = list(structure.sites[move_index].coords)
        old_position.append(structure.sites[move_index].species_string)
        old_position = deepcopy(old_position)

        # update structure

        new_structure = structure.copy()
        # new_structure.xyz_df = structure.xyz_df.copy()

        new_structure.translate_sites(move_index, move_vector, frac_coords=False)

        new_position = list(new_structure.sites[move_index].coords)
        new_position.append(new_structure.sites[move_index].species_string)
        new_position = deepcopy(new_position)

        # new_structure.update_xyz(move_index, new_position, move_vector, max_step, old_position)
        new_structure.xyz_df = xyz(new_structure)
        new_structure.move_index(move_index)

        return new_structure


def xyz(structure):

    data = []
    for i, site in enumerate(structure.sites):
        temp = [site.coords[0], site.coords[1], site.coords[2], site.species_string]
        data.append(temp)
    labels = ["x", "y", "z", "el"]

    df = pandas.DataFrame(data, columns=labels)

    df_x = df.copy().sort_values("x")
    df_y = df.copy().sort_values("y")
    df_z = df.copy().sort_values("z")

    return {"df_x": df_x, "df_y": df_y, "df_z": df_z}
