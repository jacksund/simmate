# -*- coding: utf-8 -*-

import itertools

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.prototypes.aflow import AflowPrototype

# from simmate.utilities import get_sanitized_structure, estimate_volume

from django_pandas.io import read_frame


class ExactAflowPrototypeStructures:

    """
    Given a compositon, this class can be used to create structures from
    the **exactly-matching** prototypes in the AFLOW library. This means we
    are only using prototypes that have the same anonymous formula. For example,
    if you request structures for Ca2N to be made, only prototypes that have
    the AB2 anonymoous formula will be used (such as the MoS2 prototype).
    """

    def __init__(self, composition, max_sites=115):
        # composition --> pymatgen composition object (ideally a reduced composition)
        # allow_multiples --> whether to allow structures where the reduced
        # compositions are the same, but the actual number of sites differs.
        # For example, Ca6N3 would be allow to return structures that give
        # Ca2N, Ca8N4, and so forth.
        # max_sites defaults to 115 because this would include all prototypes
        # in the aflow database (current largest is (105 sites))

        # Store these input properties for reference
        self.composition = composition
        self.max_sites = max_sites

        # ---------------------------------------------------------------------

        # First let's load all of the prototype structures that have a compatible
        # number of sites in the structure. For this we require that the prototypes
        # meet the following:
        #   (1) prototypes have the same anonymous formula as target the composition
        #   (2) the number of wykcoff sites is at least the number of target elements
        # Note: #1 ensures that #2 is true here, so we don't actually need to
        # check for both -- just #1.

        # We allow for multiples so we want all multiples nsites in our
        # desired composition. For example if our compositon, has 6 sites, we
        # would pull all prototypes that have 6, 12, 19, ..., 6*N sites.
        # First generate a list of the allow number of sites
        target_nsites_list = [
            int(composition.num_atoms * n)
            for n in range(1, (max_sites // int(composition.num_atoms)) + 1)
        ]
        # Now filter off the prototypes that have the proper number of sites
        prototype_entries = AflowPrototype.objects.filter(
            formula_anonymous=composition.anonymized_formula,
            nsites__in=target_nsites_list,
        ).all()

        # for user convience, let's store these selected prototypes as a dataframe
        # and attach it to this class instance
        self.prototype_dataframe = read_frame(prototype_entries)

        # Now that we have the prototype entries, let's convert them to
        # structure objects for us to use below.
        self.prototype_structures = [
            prototype.to_toolkit() for prototype in prototype_entries
        ]

        # ---------------------------------------------------------------------

        # We now generate all prototypes here. We store them in a final list
        # as we make them too.
        self.structures = []
        for prototype in self.prototype_structures:

            # we need to match elements in our target composition to those in
            # the prototype. For example, Ca2NF with the NaCrS2 prototype would
            # need to match S-->Ca, Cr-->N, and Na-->F.
            #
            # To do this, we need to look at every possible order of target
            # elements. We then iterate through these combinations and check
            # which ones are valid. For example, a Ca2NCl would give us possible
            # orderings of Ca-N-F, Ca-F-N, N-Ca-F, N-F-Ca, F-Ca-N, and F-N-Ca.
            # We then go through each ordering and see which ones will give our
            # target composition when substituted for Na-Cr-S in order.
            for target_elements in itertools.permutations(composition.elements):

                # Using this ordering of target elements we can now
                # attempt the subsitution for the prototype

                # We first sure to make a copy of the prototype that we can alter.
                new_structure = prototype.copy()

                # Go through and substitute out the elements
                for target_element, current_element in zip(
                    target_elements, prototype.composition
                ):
                    new_structure[current_element] = target_element

                # Now let's check to see that the final composition matches
                # what we are trying to produce. If so, we store the structure!
                # Note, we are after the reduce composition because we want
                # to allow things like Ca2NF == Ca4N2F2 as True.
                if (
                    new_structure.composition.reduced_composition
                    == composition.reduced_composition
                ):
                    self.structures.append(new_structure)

        # ---------------------------------------------------------------------

        # We now have all of the structures, but they will have unreasonable
        # volume and atomic distances right now. We iterate through each
        # and try to fix this by doing the following:
        #   (1) Scaling the structure to a predicted volume
        #   (2) Sanitizing the structure
        #   (3) [TODO] scaling the lattice vectors to avoid atoms being too close
        for i, structure in enumerate(self.structures):
            volume_guess = estimate_volume(structure.composition)
            structure.scale_lattice(volume_guess)
            structure_santized = get_sanitized_structure(structure)
            self.structures[i] = structure_santized
