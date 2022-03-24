# -*- coding: utf-8 -*-

import os
import json
import itertools
import subprocess

import numpy

from simmate.visualization.structure.blender.configuration import get_blender_command


def make_blender_structure(structure, filename="simmate_structure.blend"):

    # load the base blender command for use in function calls below
    BLENDER_COMMAND = get_blender_command()
    # OPTIMIZE: ideally I would load this outside the function so that it is only
    # loaded once. Here, I read a yaml file repeatedly. There should be a better
    # way to silently catch errors when blender isn't installed.

    # This function simply serializes a pymatgen structure object to json
    # and then calls a blender script (make_structure.py) that uses this data
    # BUG: Make sure strings are dumped using single quotes so that this
    # doesn't conflict with the command line.
    sites = json.dumps(serialize_structure_sites(structure)).replace('"', "'")
    lattice = json.dumps(structure.lattice.matrix.tolist())

    # The location of the make_structure.py
    executable_directory = os.path.dirname(__file__)
    path_to_script = os.path.join(executable_directory, "scripts", "make_structure.py")

    # Now build all of the our serialized structure data and settings together
    # into the blender command that we will call via the command line
    command = (
        f"{BLENDER_COMMAND} --background --factory-startup --python {path_to_script} "
        f'-- --sites="{sites}" --lattice="{lattice}" --save="{filename}"'
    )

    # Now run the command
    result = subprocess.run(
        command,
        shell=True,  # to access commands in the path
        capture_output=True,  # capture any ouput + error logs
    )

    return result


def serialize_structure_sites(structure):
    # NOTE: You only need to call make_blender_structure() as it calls
    # serialize_structure within it.

    # We collect all sites to draw here. Each one is this list will be a tuple
    # of... (element_symbol, radius, cartesian_coordinates)
    # For example, ("Na", 0.75, [0.5, 0.5, 0.5])
    # We also convert the coordinates from numpy to a list here.
    sites_to_draw = []

    # we repeadedly need the lattice matrix below so we just grab it upfront here
    lattice_matrix = structure.lattice.matrix

    # for each site in the structure, we want to gather all site coordinates
    # that we want to display. Note this is more than just structure.cart_coords
    # Because we want symmetrical equivalents that are also on the cell axes.
    # For example, if there a site at (0,0,0) then we also want to display the
    # site at (1,1,1).
    for site in structure:

        # Grab the base info that is the same for all site images here.
        # TODO: We fix the radius for now but may do oxidation analysis for
        # accurate ionic radii in the future
        radius = 0.75
        element = site.specie.symbol

        # first store this base site to our site collection.
        sites_to_draw.append((element, radius, site.coords.tolist()))

        # If a site has a fractional coordinate that is close to zero, then
        # that means we should duplicate the site along that edge of the lattice.
        # For example, (0, 0.5, 0.5) should be duplicated along the a-vector
        # and thus add the site (1, 0.5, 0.5).
        # We do this by checking the fractional coordinates and seeing if each
        # is close to 0.
        zero_elements = [
            i for i, x in enumerate(site.frac_coords) if numpy.isclose(x, 0, atol=0.05)
        ]

        # If more than one value is close to zero, then we need to add multiple
        # duplicate sites. For example, (0,0,0.5) would need us to add
        # (0, 1, 0.5), (1, 0, 0.5), and (1, 1, 0.5). So here we go through
        # and find all permutations that we need to add.
        permutatons = [
            combination
            for n in range(1, len(zero_elements) + 1)
            for combination in itertools.combinations(zero_elements, n)
        ]

        # Now let's iterate through each permutation and add it to our sites list
        for permutaton in permutatons:

            # make the vector that we need to add to the base site. For example,
            # if the permutation is (0,2) then we would do...
            # coords + [1, 0, 1]. Note I use fractional coords in this example
            # but use cartesians coords below.
            shift_vector = numpy.zeros(3)
            for x in permutaton:
                shift_vector = numpy.add(shift_vector, lattice_matrix[x])
            new_coords = site.coords + shift_vector
            sites_to_draw.append((element, radius, new_coords.tolist()))

        # We now repeat the above process but now with sites that have coordinate
        # that are close to 1. The key difference here is that we subract 1 instead
        # of adding 1 like we did above. e.g (1, 0.5, 0.5) becomes (0, 0.5, 0.5)
        zero_elements = [
            i for i, x in enumerate(site.frac_coords) if numpy.isclose(x, 1, atol=0.05)
        ]
        permutatons = [
            combination
            for n in range(1, len(zero_elements) + 1)
            for combination in itertools.combinations(zero_elements, n)
        ]
        for permutaton in permutatons:
            shift_vector = numpy.zeros(3)
            for x in permutaton:
                shift_vector = numpy.subtract(shift_vector, lattice_matrix[x])
            new_coords = site.coords + shift_vector
            sites_to_draw.append((element, radius, new_coords.tolist()))

    ## Add bonded sites outside of unticell
    ### Two issues exist for this code:
    #### 1. doesn't find bonded sites to atoms that were duplicated along edges
    #### 2. duplicate atoms are added to sites_to_draw
    # structure_graph = CrystalNN().get_bonded_structure(structure)
    # for n in range(len(structure_graph.structure)):
    #    connected_sites = structure_graph.get_connected_sites(n)
    #    for connected_site in connected_sites:
    #        if connected_site.jimage != (0, 0, 0):
    #            sites_to_draw.append(connected_site.site.coords)

    return sites_to_draw
