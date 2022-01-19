# -*- coding: utf-8 -*-

from numpy.random import randint, choice

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.toolkit.transformations.base import Transformation


class AtomicPermutation(Transformation):

    # Two atoms of different types are exchanged a variable number of times
    # See: https://uspex-team.org/static/file/JChemPhys-USPEX-2006.pdf

    io_scale = "one_to_one"
    ninput = 1
    use_multiprocessing = False

    #!!! should I add an option for distribution of exchange number? Potentially use creation.vector objects?
    # USPEX states that they do this - and select from a normal distribution
    def __init__(self, min_exchanges=1, max_exchanges=5):

        # save inputs for reference
        self.min_exchanges = min_exchanges
        self.max_exchanges = max_exchanges

        #!!! when doing multiple exchanges, I do not check to see if an exchange has been done before - I can change this though
        # Therefore one exchange could undo another and we could be back where we started
        # There are also scenarios where all sites are equivalent and atomic permutation cannot create a new structure
        # An example of this is NaCl, where an exchange still yields an identical structure
        # This leaves a chance that we end up with an identical structure to what we started with.
        # Therefore, I must hava a structurematcher object that I use to ensure we have a new structure
        # We try making a new structure X number of times (see max_attempts above) and if we can't, we failed to mutate the structure!
        self.structure_matcher = (
            StructureMatcher()
        )  #!!! I should lower the tolerances here!

    def apply_transformation(self, structure, max_attempts=100):

        # grab a list of the elements
        #!!! consider moving this to init to save time at the cost of more in memory
        elements = structure.composition.elements

        # This mutation is not possible for structures that have only one element
        if len(elements) == 1:
            print(
                "You cannot perform an atomic permutation on structure that only has one element type!!"
            )
            return False
        #!!! add another elif for when all sites are equivalent and atomic permutation cannot create a new structure

        for attempt in range(max_attempts):  # I could alternatively do a while loop

            # make a deepcopy of the structure so that we aren't modifying it inplace
            # this also allows us to compare the new structure to the original
            # placing this at the top of the loop also resets the structure for us each time
            new_structure = structure.copy()

            # grab a random integer within the exchange range (min/max) defined above
            nexchanges = randint(low=self.min_exchanges, high=self.max_exchanges)

            # perform an exchange of two random atom types X number of times
            for n in range(nexchanges):
                # grab two elements of different types
                element1, element2 = choice(elements, size=2)

                # select a random index of element1 and element2
                index1 = choice(new_structure.indices_from_symbol(element1.symbol))
                index2 = choice(new_structure.indices_from_symbol(element2.symbol))

                # now exchange the species type of those two sites
                new_structure.replace(index1, element2)
                new_structure.replace(index2, element1)

            # see if the new structure is different from the original!
            # check will be True if the new structure is the same as the original
            check = self.structure_matcher.fit(structure, new_structure)
            if not check:
                # we successfully make a new structure!
                return new_structure
            # else continue

        # if we make it this far, then we hit our max_attempts limit without making a new structure
        # therefore, we failed the mutation
        print("Failed to make a new structure that is different from the original")
        return False
