# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.analysis.diffusion.neb.pathfinder import DistinctPathFinder as PymatgenDPF


class DistinctPathFinder(PymatgenDPF):
    def write_all_migration_hops(self, directory: Path):
        # We write all the path files so users can visualized them if needed
        filename = directory / "all_migration_hops.cif"
        self.write_all_paths(str(filename), nimages=10)
        migration_hops = self.get_paths()
        for i, migration_hop in enumerate(migration_hops):
            number = str(i).zfill(2)  # converts numbers like 2 to "02"
            # the files names here will be like "migration_hop_02.cif"
            migration_hop.write_path(
                str(directory / f"migration_hop_{number}.cif"),
                nimages=10,  # this is just for visualization
            )
