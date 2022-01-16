# -*- coding: utf-8 -*-

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.prototypes.aflow import AflowPrototype

from django_pandas.io import read_frame


class AflowPrototypeStructures:

    """
    Given a compositon, this class can be used to create all structures from
    the prototypes in the AFLOW library.

    At the moment, this does not allow for disordered versions of prototypes.
    This would be like using a supercell of a 1-site prototype for a 2-site target
    composition. A concrete example of this is using the NaCl rocksalt prototype
    for a NaClBr or NaKClBr compositions -- each of these compositions would
    require a supercell of the NaCl prototype structure becuase they need more
    than 2 sites.
    """

    def __init__(self, composition, allow_multiples=True, max_sites=115):
        # composition --> pymatgen composition object (ideally a reduced composition)
        # allow_multiples --> whether to allow structures where the reduced
        # compositions are the same, but the actual number of sites differs.
        # For example, Ca6N3 would be allow to return structures that give
        # Ca2N, Ca8N4, and so forth.
        # max_sites defaults to 115 because this would include all prototypes
        # in the aflow database (current largest is (105 sites))

        # First let's load all of the prototype structures that have a compatible
        # number of sites in the structure.

        # There are two conditions that we need to meet for prototypes here:
        #   (1) the number of wyckoff sites is compatible with nelements OR nsites
        #   (2) the number of individual sites is compatible with nsites
        # This is because we can only insert at symmetrically unique sites (bc
        # we ignore disoreder superlattices here) and the total number of sites
        # after symmetry operations needs to match our target composition.
        # Note that nsites is *not* always a multiple of nsites_wyckoff! For
        # example the Spinel prototype has nsites=14 and nsites_wyckoff=3.

        # If we allow for multiples then  want all multiples nsites in our
        # desired composition. For example if our compositon, has 6 sites, we
        # would pull all prototypes that have 6, 12, 19, ..., 6*N sites.
        if allow_multiples:
            # First generate a list of the allow number of sites
            # We use 40 here because this the maximum number of unique wyckoff
            # sites of any prototype (actual max is 36).
            target_nsites_wyckoff_list = [
                int(composition.num_atoms * n)
                for n in range(1, (40 // len(composition.elements)) + 1)
            ]
            target_nsites_list = [
                int(composition.num_atoms * n)
                for n in range(1, (max_sites // int(composition.num_atoms)) + 1)
            ]
            # Now filter off the prototypes that have the proper number of sites
            prototype_entries = AflowPrototype.objects.filter(
                nsites_wyckoff__in=target_nsites_list,
                nsites__in=target_nsites_list,
            ).all()

        # If we don't want multiples, we can just filter by
        # an exact match for number of total sites and wyckoff sites
        else:
            prototype_entries = AflowPrototype.objects.filter(
                nsites_wyckoff=int(composition.elements),
                nsites=int(composition.num_atoms),
            ).all()

        # for user convience, let's store these selected prototypes as a dataframe
        # and attach it to this class instance
        self.prototype_dataframe = read_frame(prototype_entries)

        # Now that we have the prototype entries, let's convert them to
        # structure objects for us to use below.
        self.prototype_structures = [
            prototype.to_toolkit() for prototype in prototype_entries
        ]
