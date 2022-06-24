# -*- coding: utf-8 -*-

import itertools

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.toolkit import Composition, Structure
from simmate.database import connect
from simmate.database.third_parties import AflowPrototype


class FromAflowPrototypes:
    """
    Generates structures of a target composition by using AFLOW prototypes as
    templates.

    # EXACT MODE
    Given a compositon, this class can be used to create structures from
    the **exactly-matching** prototypes in the AFLOW library. This means we
    are only using prototypes that have the same anonymous formula. For example,
    if you request structures for Ca2N to be made, only prototypes that have
    the AB2 anonymoous formula will be used (such as the MoS2 prototype).

    # ORDERED MODE
    Allow prototypes such as PbClF to be used on compositions like Ca2N
    (i.e. 3 wyckoff sites available and 3 sites to to create). Prototypes are
    selected based on wyckoff site multiplicity.

    # DISORDERED MODE
    (Not implemented yet)
    At the moment, this does NOT allow for disordered versions of prototypes.
    This would be like using a supercell of a 1-site prototype for a 2-site target
    composition. A concrete example of this is using the NaCl rocksalt prototype
    for a NaClBr or NaKClBr compositions -- each of these compositions would
    require a supercell of the NaCl prototype structure becuase they need more
    than 2 sites.
    """

    def __init__(
        self,
        composition: Composition,
        allow_multiples: bool = True,
        max_sites: int = 115,
        mode: str = "exact",  # options are "exact" and "ordered"
    ):
        """
        #### Parameters

        - `composition`:
            The desired composition to create structures for

        - `allow_multiples`:
            Whether to allow structures where the reduced compositions are the
            same, but the actual number of sites differs. For example, Ca6N3
            would be allowed to return structures that give Ca2N, Ca8N4, and
            so forth.

        - `max_sites`:
            Maximum sites allowed in the created structures. This defaults to
            115 because this would include all prototypes in the aflow database
            (currently, the largest is prototype is 105 sites)

        - `mode`:
            The method to use for selecting prototypes. Options are "exact" and
            "ordered" (see class docstring above for what each does). Default
            is "exact"
        """

        # Store these input properties for reference
        self.composition = composition
        self.max_sites = max_sites
        self.allow_multiples = allow_multiples
        self.mode = mode

        # Load the template prototypes from the database. These methods set
        # the self.prototype_structures attribute that will be used below
        if mode not in ["exact", "ordered"]:
            raise Exception(f"mode provided ({mode}) is not allowed")
        elif mode == "exact":
            self._get_exact_prototypes()
            self._create_structures_from_exact()
        elif mode == "ordered":
            if self.allow_multiples:
                raise Exception(
                    "using allow_multiples=True with mode='ordered' often results "
                    "in millions of structures, so this input is currently not allowed."
                )
            self._get_ordered_prototypes()
            self._create_structures_from_ordered()
        # TODO: Consider breaking this into subclasses that inherit from a base
        # class. Alternatively, keep these here and allow combination of modes.

        # ---------------------------------------------------------------------

        # We now have all of the structures, but they will have unreasonable
        # volume and atomic distances right now. We iterate through each
        # and try to fix this by doing the following:
        #   (1) Scaling the structure to a predicted volume
        #   (2) Sanitizing the structure
        #   (3) [TODO] scaling the lattice vectors to avoid atoms being too close
        volume_guess = self.composition.volume_estimate()
        for i, structure in enumerate(self.structures):
            structure.scale_lattice(volume_guess)
            structure_santized = structure.get_sanitized_structure()
            self.structures[i] = structure_santized

        # ---------------------------------------------------------------------

        # lastly, go through and remove duplicate structures
        unique_structures = []
        for structure in self.structures:
            if structure not in unique_structures:
                unique_structures.append(structure)
        self.structures = unique_structures
        # OPTIMIZE: should I do a more robust check for duplicate structures?
        # For example, I could use a fingerprint validator.

    def _get_exact_prototypes(self):
        # Load all of the prototype structures that have a compatible number of
        # sites in the structure. For this we require that the prototypes
        # meet the following:
        #   (1) prototypes have the same anonymous formula as target the composition
        #   (2) the number of wykcoff sites is at least the number of target elements
        # Note: #1 ensures that #2 is true here, so we don't actually need to
        # check for both -- just #1.

        # We allow for multiples so we want all multiples nsites in our
        # desired composition. For example if our compositon, has 6 sites, we
        # would pull all prototypes that have 6, 12, 19, ..., 6*N sites.
        # First generate a list of the allow number of sites
        if self.allow_multiples:
            target_nsites_list = [
                int(self.composition.num_atoms * n)
                for n in range(
                    1, (self.max_sites // int(self.composition.num_atoms)) + 1
                )
            ]
            # Now filter off the prototypes that have the proper number of sites
            prototype_entries = AflowPrototype.objects.filter(
                formula_anonymous=self.composition.anonymized_formula,
                nsites__in=target_nsites_list,
            ).all()
        else:
            prototype_entries = AflowPrototype.objects.filter(
                formula_anonymous=self.composition.anonymized_formula,
                nsites=int(self.composition.num_atoms),
            ).all()

        # for user convience, let's store these selected prototypes as a dataframe
        # and attach it to this class instance
        self.prototype_dataframe = prototype_entries.to_dataframe()

        # Now that we have the prototype entries, let's convert them to
        # structure objects for us to use elsewhere.
        self.prototype_structures = prototype_entries.to_toolkit()

    def _get_ordered_prototypes(self):

        # Load all of the prototype structures that have a compatible
        # number of sites in the structure.

        # There are two conditions that we need to meet for prototypes here:
        #   (1) the number of wyckoff sites is compatible with nelements OR nsites
        #   (2) the number of individual sites is compatible with nsites
        # This is because we can only insert at symmetrically unique sites (bc
        # we ignore disoreder superlattices here) and the total number of sites
        # after symmetry operations needs to match our target composition.
        # Note that nsites is *not* always a multiple of nsites_wyckoff! For
        # example the Spinel prototype has nsites=14 and nsites_wyckoff=3.

        # Generate a list of the allowed number of wyckoff sites
        # We use 40 here because this the maximum number of unique wyckoff
        # sites of any prototype (actual max is 36).
        target_nsites_wyckoff_list = set(
            [
                int(self.composition.num_atoms * n)
                for n in range(1, (40 // len(self.composition.elements)) + 1)
            ]
            + [
                int(len(self.composition.elements) * n)
                for n in range(1, (40 // int(self.composition.num_atoms)) + 1)
            ]
        )

        # If we allow for multiples then  want all multiples nsites in our
        # desired composition. For example if our compositon, has 6 sites, we
        # would pull all prototypes that have 6, 12, 18, ..., 6*N sites.
        if self.allow_multiples:
            # First generate a list of the allow number of sites
            target_nsites_list = [
                int(self.composition.num_atoms * n)
                for n in range(
                    1, (self.max_sites // int(self.composition.num_atoms)) + 1
                )
            ]
            # Now filter off the prototypes that have the proper number of sites
            prototype_entries = AflowPrototype.objects.filter(
                nsites_wyckoff__in=target_nsites_wyckoff_list,
                nsites__in=target_nsites_list,
            ).all()

        # If we don't want multiples, we can just filter by
        # an exact match for number of total sites and wyckoff sites
        else:
            prototype_entries = AflowPrototype.objects.filter(
                nsites_wyckoff__in=target_nsites_wyckoff_list,
                nsites=int(self.composition.num_atoms),
            ).all()

        # for user convience, let's store these selected prototypes as a dataframe
        # and attach it to this class instance
        self.prototype_dataframe = prototype_entries.to_dataframe()

        # Now that we have the prototype entries, let's convert them to
        # structure objects for us to use below.
        # Note, becuase the ordered method relies on wyckoff sites, we want
        # these as symmetrized structures.
        self.prototype_structures = [
            SpacegroupAnalyzer(prototype).get_symmetrized_structure()
            for prototype in prototype_entries.to_toolkit()
        ]

    def _create_structures_from_exact(self):
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
            for target_elements in itertools.permutations(self.composition.elements):

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
                    == self.composition.reduced_composition
                ):
                    self.structures.append(new_structure)

    def _create_structures_from_ordered(self):

        # Create a flattened list of elements (e.g. Ca2N --> [Ca, Ca, N])
        # Note we use the reduced composition to ensure the smallest list, and
        # we duplicate this list to the proper size based on the prototype
        # being used.
        element_list = self.composition.reduced_composition.elements
        element_list_expanded = []
        for element in self.composition.reduced_composition.elements:
            element_list_expanded += [element] * int(self.composition[element])

        self.structures = []
        for prototype in self.prototype_structures:

            if len(prototype.equivalent_indices) % len(element_list_expanded) == 0:
                mult = len(prototype.equivalent_indices) // len(element_list_expanded)
                element_list_scaled = element_list_expanded * mult
            elif len(prototype.equivalent_indices) % len(element_list) == 0:
                mult = len(prototype.equivalent_indices) // len(element_list)
                element_list_scaled = element_list * mult
            else:
                raise Exception("Unknown scaling for prototype wyckoffs")

            for target_elements in itertools.permutations(element_list_scaled):

                new_structure = prototype.copy()

                # Go through and substitute out the elements
                for target_element, current_indicies in zip(
                    target_elements, prototype.equivalent_indices
                ):
                    for current_index in current_indicies:
                        new_structure.replace(current_index, target_element)

                # Now let's check to see that the final composition matches
                # what we are trying to produce. If so, we store the structure!
                # Note, we are after the reduce composition because we want
                # to allow things like Ca2NF == Ca4N2F2 as True.
                if (
                    new_structure.composition.reduced_composition
                    == self.composition.reduced_composition
                ):
                    # convert from symmetrized structure back to toolkit structure
                    new_structure_toolkit = Structure(
                        lattice=new_structure.lattice,
                        species=new_structure.species,
                        coords=new_structure.frac_coords,
                    )
                    self.structures.append(new_structure_toolkit)
