# -*- coding: utf-8 -*-

"""
These are common utilies that I use throughout other scripts/classes. Each function
gives back some estimated value (in no particular format) that is based entirely
off of the composition -- note this composition is a materials project composition object.
"""

import warnings

import numpy


def estimate_radii(composition, radius_method="ionic"):

    # grab the elements as a list of Element objects
    elements = composition.elements

    # change the list of elements to radii list (atomic/vdw/metallic/ionic)
    if radius_method == "atomic":
        radii = [element.atomic_radius for element in elements]
    elif radius_method == "atomic_calculated":
        radii = [element.atomic_radius_calculated for element in elements]
    elif radius_method == "van_der_waals":
        radii = [element.van_der_waals_radius for element in elements]
    elif radius_method == "metallic":
        #!!! BUG: gives an error with Mg4Si4O12
        radii = [element.metallic_radius for element in elements]
    elif radius_method == "ionic":
        # little more complicated here because we need to predict oxidation states
        # there are different ways to do this, but for now just base it off the composition alone
        # alternative methods are often structure dependent (i.e. pymatgen.analysis.bond_valence methods)
        # this line changes composition to be composed of Specie objects instead of Element objects
        #!!! should I overwrite the self.composition above?
        # By converting to the reduced_composition first, we see a massive speed up -- this is done with max_sites=-1
        #!!! oxidation prediction struggles with electrides -- we would want to add target_charge=1 for these
        composition = composition.add_charges_from_oxi_state_guesses(max_sites=-1)
        elements = composition.elements
        #!!! if the estimated oxidation state is zero, I grab the atomic radius. Should I do something like average_ionic_radius instead?
        #!!! BUG -- H+, Si4-,... do not have an ionic radius...
        # radii = [e.ionic_radius if e.oxi_state != 0 else e.element.atomic_radius for e in elements]
        # This will print a lot of warnings when the ionic radius doesn't exist. I expect these warnings, so I choose to suppress them here
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # dont print the warnings!
            radii = []
            for e in elements:
                # attempt to grab the ionic_radius
                r = e.ionic_radius
                # if None is return, then we have an error
                if not r:
                    # grab the atomic radius instead #!!! is this a good assumed fix?
                    r = e.element.atomic_radius
                radii.append(r)
    #!!! Some elements have "None" for a radius type. For example, Yttrium doesn't have a vdw radius listed in PyMatGen
    #!!! Errors are also thrown when you have unexpected oxidation states and ionic radius - like with electrides (Ca2N, Y2C)
    if None in radii:
        print(
            "The radii type specified is not allowed for one or more of the elements in composition"
        )
        return False

    #!!! this returns a list of numbers, where the order is assumed the same as the order of elements in composition
    return radii


def estimate_volume(composition, radius_method="ionic", packing_factor=1.35):

    # 1.35 is 74% packing efficieny (hexagonal packing) - should I make this the target volume or something larger?

    # grab a list of radii (assumed to be in order of elements in composition)
    radii = estimate_radii(composition, radius_method)

    # take the radii and find the corresponding spherical volume for each atom type
    volumes = [4 / 3 * numpy.pi * (radius ** 3) for radius in radii]

    # find the total volume of all spheres in the composition
    total_volume = sum(
        [
            composition[element] * volume
            for element, volume in zip(composition.elements, volumes)
        ]
    )
    # based on the packing of these spheres, we want to scale the volume of the lattice
    # better packing corresponds to a lower packing_factor
    total_volume *= packing_factor

    return total_volume


def distance_matrix(composition, radius_method="ionic", packing_factor=0.5):

    # grab a list of radii (assumed to be in order of elements in composition)
    radii = estimate_radii(composition, radius_method)

    # multiply the radii by some factor that you want limit the overlap by
    # for example, if we don't want sites any closer than 50% their radii so set factor=0.5
    radii = [
        float(radius * packing_factor) for radius in radii
    ]  #!!! float() strips the unit (ang) from the value to avoid errors... is that okay?

    # create the element distance matrix
    # see USPEX input option IonDistances (matrix) for analogy
    # to make the full matrix, we'd use itertools.product()
    # but the matrix is a mirror about the diagonal axis, so we really only need half the matrix
    # because of this, we could get away with itertools.combinations_with_replacement() if speed was an issue
    # since speed isn't an issue, I'm using product anyways
    # combos = itertools.product(elements, repeat=2)
    ###
    # There doesn't seem to be an easy way to get iterools.product() to a matrix...
    # so I'm doing it without itertools which is slower
    matrix = []
    for radius1 in radii:
        row = []
        for radius2 in radii:
            limit = radius1 + radius2
            row.append(limit)
        matrix.append(row)
    # convert the result list of list matrix to a numpy array (so it is much faster in referencing later)
    element_distance_matrix = numpy.array(matrix)
    return element_distance_matrix
