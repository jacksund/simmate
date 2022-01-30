# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Structure

from pymatgen.analysis.diffusion.neb.pathfinder import (
    DistinctPathFinder,
    MigrationHop,
    IDPPSolver,
)

from typing import List


class MigrationImages:
    """
    This class is just a list of structures for a diffusion pathway.

    Note, this class is primarily used to generate inputs for calculations. If
    you'd like more advanced features, you should represent your diffusion
    pathway as a MigrationHop instead.
    """

    def __init__(self, migrating_specie: str, structures: List[Structure]):
        self.migrating_specie = migrating_specie
        self.structures = structures

    def get_sum_structure(self):

        # OPTIMIZE: this is very inefficient. It's much faster to visualize
        # structures with MigrationHop class because you know which atom is
        # moving. Here, we need to treat all atoms as moving. We can also
        # speed this up by only looking at diffusing species too.
        final_coords = []
        final_species = []
        for structure in self.structures:
            for site in structure:
                is_new = True
                for coords in final_coords:
                    if all(
                        numpy.isclose(
                            site.frac_coords,
                            coords,
                            rtol=1e-03,
                            atol=1e-03,
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
        migration_hop: MigrationHop,
        vac_mode: bool = True,
        min_nsites: int = 80,
        max_nsites: int = 240,
        min_length: int = 10,
    ):
        # The third thing returned is the bulk_supercell which we don't need.
        start_supercell, end_supercell, _ = migration_hop.get_sc_structures(
            vac_mode=vac_mode,
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
            migrating_specie=str(migration_hop.isite.specie),
        )

    @classmethod
    def from_endpoints(
        cls,
        structure_start: Structure,
        structure_end: Structure,
        nimages: int,
        migrating_specie: str,
        **kwargs,
    ):
        # Run IDPP relaxation on the images before returning them
        idpp_solver = IDPPSolver.from_endpoints(
            [structure_start, structure_end],
            nimages=nimages,
        )
        images = idpp_solver.run()

        return cls(migrating_specie, images)

    @classmethod
    def from_indicies(
        cls,
        structure: Structure,
        index_start: int,
        index_end: int,
        **kwargs,
    ):
        # This information is all we need for a MigrationHop object
        pathway = MigrationHop(index_start, index_end, structure)
        return cls.from_migration_hop(pathway)

    @classmethod
    def from_structure(
        cls,
        structure: Structure,
        migrating_specie: str,
        vac_mode: bool = True,  # vacancy vs. interstitial diffusion
        min_nsites: int = 80,  # supercell must have at least this many atoms
        max_nsites: int = 240,  # supercell must NOT have this many atoms
        min_length: int = 10,  # supercell must have vectors of at least this length
        **kwargs,
    ):
        # convert to the LLL reduced primitive cell to make it as cubic as possible
        structure_lll = structure.get_sanitized_structure()

        # Use pymatgen to find all the symmetrically unique pathways.
        # NOTE: This only finds pathways up until the structure is percolating.
        # If you are interested in longer pathways, then this script needs to
        # be adjusted by passing additional kwargs
        pathfinder = DistinctPathFinder(
            structure_lll,
            migrating_specie=migrating_specie,
            **kwargs,
        )
        pathways = pathfinder.get_paths()

        # Now go through each path and convert to a MigrationPath. We return
        # these as a list of paths.
        migration_paths = []
        for pathway in pathways:

            migration_path = cls.from_migration_hop(
                migration_hop=pathway,
                vac_mode=vac_mode,
                min_nsites=min_nsites,
                max_nsites=max_nsites,
                min_length=min_length,
            )
            migration_paths.append(migration_path)

        return migration_paths
