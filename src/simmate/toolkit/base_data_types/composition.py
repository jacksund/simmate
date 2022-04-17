# -*- coding: utf-8 -*-

"""
This module defines the Composition class.

It is a very basic extension PyMatGen's core Composition class, as it only adds
a few extra methods and does not change any other usage. Note that this class
is currently NOT used by Simmate's Structure class. For Simmate, 
Structure.composition will still return a pymatgen composition object.
"""

import warnings
import itertools
from typing import List

import numpy

from pymatgen.core import Composition as PymatgenComposition


class Composition(PymatgenComposition):
    # Leave docstring blank and just inherit from pymatgen

    def radii_estimate(self, radius_method: str = "ionic"):
        """
        Gives the reported radii for each element in the composition.

        #### Parameters

        - `radius_method` :
            Options are atomic; atomic_calculated; van_der_waals; metallic; ionic.
            The default is "ionic".

        #### Returns

        - `radii` :
            A list of radii in the same order as composition.elements
        """

        # change the list of elements to radii list (atomic/vdw/metallic/ionic)
        if radius_method == "atomic":
            radii = [element.atomic_radius for element in self.elements]
        elif radius_method == "atomic_calculated":
            radii = [element.atomic_radius_calculated for element in self.elements]
        elif radius_method == "van_der_waals":
            radii = [element.van_der_waals_radius for element in self.elements]
        elif radius_method == "metallic":
            radii = [
                element.metallic_radius if element.is_metal else None
                for element in self.elements
            ]
        elif radius_method == "ionic":
            # In order to predict the radius here, we first need to predict the
            # oxidation states. Note that this prediction changes composition to
            # be made of Specie objects instead of Element objects.
            # By converting to the reduced_composition first, we see a massive speed
            # up -- this is done with max_sites=-1
            composition_oxi = self.add_charges_from_oxi_state_guesses(max_sites=-1)
            # Now we can grab the predicted radii
            # If the estimated oxidation state is zero OR if the predicted oxidation
            # state does not have an available radius (e.g H+ doesn't have a reported
            # radius in our dataset), I grab the atomic radius.
            # BUG: This will print a lot of warnings when the ionic radius doesn't exist.
            # I expect these warnings, so I choose to suppress them here.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # dont print the warnings!
                radii = []
                for element in composition_oxi.elements:
                    # attempt to grab the radius
                    radius = element.ionic_radius
                    # if the radius is None, then we have an error and should grab
                    # the atomic radius instead
                    if not radius:
                        # note the .element is because we have our element
                        # variable as a Specie object right now.
                        radius = element.element.atomic_radius
                    radii.append(radius)
        # Some methods above might not give a radius for elements. For example,
        # N will not provide a Metallic radius. In cases like this, we should let
        # the user know.
        if None in radii:
            raise Exception(
                f"{radius_method} radius_method is not allowed for one or more"
                " of the elements in composition"
            )
        # this returns a list of radii, where the order is assumed the same as the
        # order of elements in composition
        return radii

    def volume_estimate(
        self,
        radius_method: str = "ionic",
        packing_factor: float = 1.35,
    ):
        """
        Gives a predicted lattice volume using the reported radii for each
        element in the composition.

        #### Parameters

        - `radius_method` :
            Options are atomic; atomic_calculated; van_der_waals; metallic; ionic.
            The default is "ionic".
        - `packing_factor` :
            Scaling value for the volume in relation to predict ionic radii.
            A value of 1 means the total volume will be exactly same as the sum
            of all spheres. Larger values will give smaller volumes. The
            default is 1.35, which is 74% packing efficiency (hexagonal packing).

        #### Returns

        - `total_volume` :
            the estimated volume for a unitcell of this composition
        """

        # grab a list of radii (assumed to be in order of elements in composition)
        radii = self.radii_estimate(radius_method)

        # take the radii and find the corresponding spherical volume for each atom type
        volumes = [4 / 3 * numpy.pi * (radius**3) for radius in radii]

        # find the total volume of all spheres in the composition
        total_volume = sum(
            [self[element] * volume for element, volume in zip(self.elements, volumes)]
        )
        # based on the packing of these spheres, we want to scale the volume of the
        # lattice better packing corresponds to a lower packing_factor
        total_volume *= packing_factor

        return total_volume

    def distance_matrix_estimate(
        self,
        radius_method: str = "ionic",
        packing_factor: float = 0.5,
    ):
        """
        Gives the estimated element-element distances using the reported radii
        for each element in the composition.

        For example, Mg-O-F would give a symmetric matrix like...

        |    | Mg   | O    | F    |
        | Mg | 1.5  | 1.05 | 1.   |
        | O  | 1.05 | 0.6  | 0.55 |
        | F  | 1.   | 0.55 | 0.5  |

        #### Parameters

        - `radius_method` :
            Options are atomic; atomic_calculated; van_der_waals; metallic; ionic.
            The default is "ionic".
        - `packing_factor` :
            Scaling value for the volume in relation to predict ionic radii.
            A value of 1 means the total volume will be exactly same as the sum
            of all spheres. Larger values will give smaller volumes. Because this
            method is commonly used to define minimum possible distances for
            random structure creation, we make the default 0.5.

        #### Returns

        - `element_distance_matrix` :
            A matrix of element-element distances
        """

        # grab a list of radii (assumed to be in order of elements in composition)
        radii = self.radii_estimate(radius_method)

        # multiply the radii by some factor that you want limit the overlap by
        # for example, if we don't want sites any closer than 50% their radii so
        # we can set factor=0.5.
        # Note, float() strips the unit (ang) from the value to avoid errors.
        radii = [float(radius * packing_factor) for radius in radii]

        # Create the element distance matrix
        # There doesn't seem to be an easy way to get iterools.product() to a matrix
        # so I iterate through the possible combinations manually.
        # OPTIMIZE: note this is really a symmetrical matrix so I'm actually caclulating
        # things twice.
        matrix = []
        for radius1 in radii:
            row = []
            for radius2 in radii:
                limit = radius1 + radius2
                row.append(limit)
            matrix.append(row)
        # convert the result matrix of list matrix to a numpy array before returning
        element_distance_matrix = numpy.array(matrix)
        return element_distance_matrix

    @property
    def chemical_subsystems(self) -> List[str]:
        """
        Returns all chemical systems of this composition's chemical system.

        For example, Y2C has the chemical system "Y-C" and would return
        ["Y", "C", "C-Y"]. Note that the returned list has elements of a given
        system in alphabetical order (i.e. it gives "C-Y" and not "Y-C")

        #### Returns

        - `subsystems`:
            A list of chemical systems that make up the input chemical system.
        """

        # TODO: this will may be better located elsewhere. Maybe even as a method for
        # the Composition class.

        # Convert the system to a list of elements
        system_cleaned = self.chemical_system.split("-")

        # Now generate all unique combinations of these elements. Because we also
        # want combinations of different sizes (nelements = 1, 2, ... N), then we
        # put this in a for-loop.
        subsystems = []
        for i in range(len(system_cleaned)):
            # i is the size of combination we want. We now ask for each unique combo
            # of elements at this given size.
            for combo in itertools.combinations(system_cleaned, i + 1):
                # Combo will be a tuple of elements that we then convert back to a
                # chemical system. We also sort this alphabetically.
                #   ex: ("Y", "C", "F") ---> "C-F-Y"
                subsystem = "-".join(sorted(combo))
                subsystems.append(subsystem)
        return subsystems
