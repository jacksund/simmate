# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Structure

from pymatgen.analysis.diffusion.neb.pathfinder import (
    DistinctPathFinder,
    MigrationHop as PymatgenMigrationHop,
    IDPPSolver,
)

from typing import List


class MigrationImages(list):
    """
    This class is just a list of structures for a diffusion pathway. It has
    utility methods to help create these structures but otherwise behaves
    exactly like a python list.

    Note, this class is primarily used to generate inputs for calculations. If
    you'd like more advanced features, you should represent your diffusion
    pathway as a MigrationHop instead.As a rule of thumb: Only use this class
    if you are manually creating your pathway from endpoint supercells or from
    a set of supercell images.

    All MigrationHop's can be converted to MigrationImages (using the
    `from_migration_hop` method); but not all MigrationImages can be converted
    to MigrationHops.
    """

    def __init__(self, structures: List[Structure]):
        # This init function does nothing except apply typing -- specifically,
        # it says that it expects a list of structures.
        super().__init__(structures)

    def get_sum_structure(self, tolerance: float = 1e-3):
        """
        Takes all structures and combines them into one. Atoms that are within
        the given tolerance are joined into a single site.

        This is primarily used to view a diffusing pathway within a single
        structure -- as well as how the host lattice changes during diffusion.
        If you are able to convert your pathway to a MigrationHop, the
        MigrationHop.write_path() method is much faster and cleaner than this
        method, so it should be preffered. Also, because there are many atoms
        that are overlapping here, the output structure may cause programs
        like VESTA to crash.

        #### Parameters

        - `tolerance`:
            the angle and distance tolerance to consider fractional coordinates
            as matching. Matching sites will be merged as 1 site in the final
            sum structure.
        """

        # OPTIMIZE: this is very inefficient. It's much faster to visualize
        # structures with MigrationHop class because you know which atom is
        # moving. Here, we need to treat all atoms as moving. We can also
        # speed this up by only looking at diffusing species too.
        final_coords = []
        final_species = []
        for structure in self:  # recall self is a list of structures
            for site in structure:
                is_new = True
                for coords in final_coords:
                    if all(
                        numpy.isclose(
                            site.frac_coords,
                            coords,
                            rtol=tolerance,
                            atol=tolerance,
                        )
                    ):
                        is_new = False
                        break
                if is_new:
                    final_coords.append(site.frac_coords)
                    final_species.append(site.specie)

        structure = Structure(
            lattice=structure.lattice,
            species=final_species,
            coords=final_coords,
        )

        return structure

    @staticmethod
    def get_nimages(
        pathway_length: float,
        min_image_step: float = 0.7,
        require_midpoint: bool = True,
    ):
        """
        Gives the desirable number of images (not including start/end structures).

        This method helps generate a MigrationImages object, and typically is
        not called directly. The other classmethods of MigrationImages call
        this for you.

        #### Parameters

        - `pathway_length`:
            The length of the pathway.

        - `min_image_step`:
            The minimum step distance for the diffusing atom between images.
            The default is 0.7 Angstroms. For example, a path 2.8A long would
            require at least 4 images for this default.

        - `require_midpoint`:
            Whether there should be an image at the midpoint. In other words,
            whether the number of images should be odd. This is often important
            if you expect the transition state to be at the midpoint and you are
            not running CI-NEB. The default is True.

        Returns
        -------

        - `nimages`:
            The number of images to use for this pathway.

        """
        # At a minimum, we want to have images be 0.7 angstroms apart, and
        # with one additional image.
        nimages = pathway_length // min_image_step + 1

        # We also want an odd number of images. This ensures we have an image
        # at exactly the midpoint, which is often necessary if we aren't
        # running CI-NEB.
        if require_midpoint and nimages % 2 == 0:
            nimages += 1

        # This is a float but it makes more sense to have an integer
        return int(nimages)

    @classmethod
    def from_migration_hop(
        cls,
        migration_hop: PymatgenMigrationHop,
        vacancy_mode: bool = True,
        min_nsites: int = 80,
        max_nsites: int = 240,
        min_length: int = 10,
        **kwargs,
    ):
        """
        Creates a MigrationImages object from a MigrationHop object

        #### Parameters

        - `migration_hop`:
            The MigrationHop object that should be converted.

        - `vacancy_mode`:
            Whether to use single-vacancy diffusion (True) or interstitial
            diffusion (False). The default is True.

        - `min_nsites`:
            The minimum number of sites to have in the supercell structure.
            The default is 80.

        - `max_nsites`:
            The maximum number of sites to have in the supercell structure.
            The default is 240.

        - `min_length`:
            The minimum length for each vector in the supercell structure.
            The default is 10 Angstroms.

        - `**kwargs`:
            Any arguments that are normally accepted by IDPPSolver
        """
        # The third thing returned is the bulk_supercell which we don't need.
        start_supercell, end_supercell, _ = migration_hop.get_sc_structures(
            vac_mode=vacancy_mode,
            min_atoms=min_nsites,
            max_atoms=max_nsites,
            min_length=min_length,
        )

        # calculate the number of images required
        nimages = cls.get_nimages(migration_hop.length)

        return cls.from_endpoints(
            start_supercell,
            end_supercell,
            nimages=nimages,
            **kwargs,
        )

    @classmethod
    def from_endpoints(
        cls,
        structure_start: Structure,
        structure_end: Structure,
        nimages: int,
        **kwargs,
    ):
        """
        Creates a MigrationImages object from start and end supercell structures.
        You do not need to specify the diffusing atom(s) as all sites are
        linearly interpolated and then relaxed by IDPP.

        #### Parameters

        - `structure_start`:
            The starting supercell of the diffusion pathway.

        - `structure_end`:
            The ending supercell of the diffusion pathway.

        - `nimages`:
            The number of desired images for the pathway. Note, if you know the
            pathway length of your path, you can use the `get_nimages` static
            method to get a logical number of images.

        - `**kwargs`:
            Any arguments that are normally accepted by IDPPSolver
        """

        # Run IDPP relaxation on the images before returning them
        idpp_solver = IDPPSolver.from_endpoints(
            [structure_start, structure_end],
            nimages=nimages,
            **kwargs,
        )
        images = idpp_solver.run()

        return cls(images)

    @classmethod
    def from_startend_sites(
        cls,
        structure: Structure,
        site_start: int,
        site_end: int,
        **kwargs,
    ):
        """
        Creates a MigrationImages object from a bulk structure and start/end
        periodic sites of the diffusing atom.

        For example, this would allow a diffusion pathway that goes from a site
        at (0,0,0) to (1,1,1). Thus, symmetry and periodic boundry conditions
        are considered.

        Note, this method just creates a MigrationHop and then uses the
        `from_migration_hop` method to make a MigrationImages object.

        #### Parameters

        - `structure`:
            The bulk crystal structure (NOT the supercell).

        - `site_start`:
            The starting periodic site for this pathway.

        - `site_end`:
            The end periodic site for this pathway.

        - `**kwargs`:
            Any arguments that are normally accepted by `from_migration_hop`.
        """
        # This information is all we need for a MigrationHop object
        pathway = PymatgenMigrationHop(site_start, site_end, structure)
        return cls.from_migration_hop(pathway, **kwargs)

    @classmethod
    def from_structure(
        cls,
        structure: Structure,
        migrating_specie: str,
        pathfinder_kwargs: dict = {},
        **kwargs,
    ):
        """
        Given a bulk crystal structure, this will find all symmetrically
        unique pathways and return them as list of MigrationImages objects.

        #### Parameters

        - `structure`:
            The bulk crystal structure (NOT the supercell).

        - `migrating_specie`:
            The identity of the diffusing ion (e.g. "Li" or "Li1+"). Note, only
            provide oxidation state if you are using an oxidation-state decorated
            structure.

        - `pathfinder_kwargs`:
            Any arguments that are normally accepted by DistinctPathFinder, but
            given as a dictionary. The default is {}.

        - `**kwargs`:
            Any arguments that are normally accepted by `from_migration_hop`.
        """
        # convert to the LLL reduced primitive cell to make it as cubic as possible
        structure_lll = structure.get_sanitized_structure()

        # Use pymatgen to find all the symmetrically unique pathways.
        # NOTE: This only finds pathways up until the structure is percolating.
        # If you are interested in longer pathways, then this script needs to
        # be adjusted by passing additional kwargs
        pathfinder = DistinctPathFinder(
            structure_lll,
            migrating_specie=migrating_specie,
            **pathfinder_kwargs,
        )
        pathways = pathfinder.get_paths()

        # Now go through each path and convert to a MigrationPath. We return
        # these as a list of paths.
        migration_paths = []
        for pathway in pathways:

            migration_path = cls.from_migration_hop(
                migration_hop=pathway,
                **kwargs,
            )
            migration_paths.append(migration_path)

        return migration_paths

    @classmethod
    def from_dynamic(cls, migration_images):
        """
        This is an experimental feature. The code here is a repurposing of
        Structre.from_dynamic so consider making a general class for
        from_dynamic methods.
        """
        is_from_past_calc = False

        # assume any list is in the MigrationHop format if there are more than
        # two structures (i.e. there is at least one midpoint image)
        if isinstance(migration_images, list) and len(migration_images) > 2:
            migration_images_cleaned = migration_images

        else:
            raise Exception(
                "Unknown format provided for migration_images input."
                f"The following was provided: {str(migration_images)} of type "
                f"{type(migration_images)}"
            )

        migration_images_cleaned.is_from_past_calc = is_from_past_calc

        return migration_images_cleaned

    def as_dict(self):
        return [s.as_dict() for s in self]
