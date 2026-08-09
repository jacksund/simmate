# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Structure


def clean_start_end_images(
    structure_start: Structure,
    structure_end: Structure,
    tolerance: float = 0.001,
):
    """
    Given two endpoint structures, this orders all sites to be the same and places
    the single moving site last in the structure.

    This function assumes all sites have an exact match in the second structure
    EXCEPT for a single site (which is the moving one).
    """

    # NOTES: code below is to help debugging
    # check if the order is already correct. If so, just skip this method
    # dists_orig = numpy.array(
    #     [s2.distance(s1) for s1, s2 in zip(structure_start, structure_end)]
    # )
    # if numpy.count_nonzero(dists_orig) == 1:
    #     return structure_start, structure_end

    base_structure = []

    starting_indicies = []
    ending_indicies = []
    for i1, site1 in enumerate(structure_start):
        found_match = False
        for i2, site2 in enumerate(structure_end):
            if site1.distance(site2) <= 0.001:
                base_structure.append(site1)
                found_match = True
                starting_indicies.append(i1)
                ending_indicies.append(i2)
                break
        # as a double-check, we keep track of the moving site
        if not found_match:
            moving_site_i = site1

    # find the indicies of the start/end moving site
    for i_start in range(len(structure_start)):
        if i_start not in starting_indicies:
            # make sure we have an agreement between the moving site found above and here
            assert structure_start[i_start] == moving_site_i
            break
    for i_end in range(len(structure_end)):
        if i_end not in ending_indicies:
            moving_site_e = structure_end[i_end]
            break

    structure_start_new = Structure.from_sites(base_structure + [moving_site_i])
    structure_end_new = Structure.from_sites(base_structure + [moving_site_e])

    # Make sure we successfully ordered the structure
    dists_new = numpy.array(
        [s2.distance(s1) for s1, s2 in zip(structure_start_new, structure_end_new)]
    )
    if not numpy.count_nonzero(dists_new) == 1:
        raise Exception("Failed to order supercell sites properly")

    return structure_start_new, structure_end_new
