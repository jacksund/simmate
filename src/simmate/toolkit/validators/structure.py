# -*- coding: utf-8 -*-

##############################################################################

import numpy
import itertools

from simmate.toolkit.validators.base import Validator

##############################################################################


class SiteDistance(Validator):
    def __init__(self, distance_cutoff):

        self.distance_cutoff = distance_cutoff

    def check_structure(self, structure):

        # NEED A BETTER WAY TO DO THIS!
        # but to check the min distance of sites, I need to ignore the diangonal (which is also made of zeros)
        dm = structure.distance_matrix
        nonzeros = dm[numpy.nonzero(dm)]
        min_distance = nonzeros.min()

        # check if min is larger than a tolerance
        check = min_distance >= self.distance_cutoff

        return check


##############################################################################


class SiteDistanceMatrix(Validator):
    def __init__(
        self,
        composition,
        radius_method="ionic",
        packing_factor=0.5,  # options unique to this class
    ):

        # save inputs for reference
        self.composition = composition
        self.radius_method = radius_method
        self.packing_factor = packing_factor

        # using our base predictor, make the distance matrix
        self.element_distance_matrix = composition.distance_matrix_estimate(
            radius_method,
            packing_factor,
        )

        #!!! BUG - If I use the ionic radius method, I should convert compositions and structures to the oxidation-state-decorated structures!
        # Logical errors will happen because composition changes - for example, Mg4Si8O12 has Mg2+4 Si4-2 Si4+6 O2-12.
        # This gives a 4x4 distance matrix, which won't match up to the expected 3x3 of a non-decorated structure.
        # For this reason, I have the default radius method set to atomic. IONIC SHOULD NOT BE SELECTED AT THE MOMENT!!!!
        #!!! quick BUG fix - this is not the best fix though (see comment above)
        # With this fix, elements predicted to have different oxidation states
        # will be restricted to only their smallest type.
        # For example, if Nitrogen is predicted to have Specie N3+, Specie N5+, Specie N3-
        # then a column is made for each of these species in the distnace matrix.
        # But because I don't convert the structure to an oxidation-state-decorated structure
        # in the check_structure() function below, all Nitrogens are checked for all of these
        # different species. Thus we are doing repeat checks and the smallest radius specie is
        # the only one having a real effect (as it sets the true min distance)
        if radius_method == "ionic":
            self.composition = composition.add_charges_from_oxi_state_guesses(
                max_sites=-1
            )

    def check_structure(self, structure):
        # now using the matrix above, we need to look at the structure
        # and determine if there are any distances that are below matrix limits
        # to save time, we want to iterate through each site and see that the site meets all requirements
        # as soon as any requirement is failed for any site, the whole loop ends
        #!!! This function is slow.
        # Maybe instead of making all comparisons, we can only look at nearest neighbors

        # we get a massive speedup if we make this matrix upfront
        # for extremely large structures with many sites, this might not be the case though - I still need to test for that
        dm = structure.distance_matrix

        # go through each element-element combo and check distances
        for i1, element1 in enumerate(self.composition):
            element1_indicies = structure.indices_from_symbol(element1.symbol)
            for i2, element2 in enumerate(self.composition):
                # grab the cutoff distance for these two specie/element types
                dist_cutoff = self.element_distance_matrix[i1][i2]
                element2_indicies = structure.indices_from_symbol(element2.symbol)
                combos = itertools.product(element1_indicies, element2_indicies)
                for s1, s2 in combos:
                    # skip if we are looking at the same site
                    if s1 == s2:
                        continue
                    # grab the periodic sites
                    # NOTE: sites here are PeriodicSite objects, not Site objects
                    # This is extremely important because we want nearest image distance, which might not be in an adjacent cell!
                    # site1 = structure[s1]
                    # site2 = structure[s2]
                    # Now get the distance between the two periodic sites
                    # distance = site1.distance(site2)
                    distance = dm[s1][s2]
                    # compare the distance to the cutoff matrix
                    if distance < dist_cutoff:
                        # one False is enough to stop - end the whole function
                        return False
        # the function will only reach this point if all distance criteria are met
        return True


##############################################################################

# # distance cutoff matrix based on USPEX (used inputgenerator)
# # read this matrix with the following:
# #    Mg Si O
# # Mg
# # Si
# # O
# dist_cut_matrix = numpy.array([[1.13, 1.06, 0.96],
#                                [1.06, 0.98, 0.89],
#                                [0.96, 0.89, 0.79]])

##############################################################################
