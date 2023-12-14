# -*- coding: utf-8 -*-

from simmate.apps.badelf.core import Grid, VoxelAssignmentToolkit, PartitioningToolkit, ElectrideFinder
from pathlib import Path

class BadElfToolkit:
    
    def __init__(
            self,
            partitioning_grid: Grid,
            charge_grid: Grid,
            directory: Path,
            partitioning: dict = None,
            algorithm: str = "badelf",
            find_electrides: bool = True,
                        ):
        self.partitioning_grid = partitioning_grid
        self.charge_grid = charge_grid
        self.directory = directory
        self.algorithm = algorithm
        
        
        # if partitioning is None:
        #     partitioning = PartitioningToolkit(partitioning_grid).get_partitioning()
        
    def from_files(
            self,
            directory: Path = Path("."),
            partitioning_file: str = "ELFCAR",
            charge_file: str = "CHGCAR",
            algorithm: str = "badelf"            
            ):
        """
        Creates a BadElfToolkit instance from the requested partitioning file
        and charge file.
        
        Args:
            directory (Path): The path to the directory that the badelf analysis
                will be located in.
            partitioning_file (str): The filename of the file to use for 
                partitioning. Must be a VASP CHGCAR or ELFCAR type file.
            charge_file (str): The filename of the file containing the charge
                information. Must be a VASP CHGCAR or ELFCAR type file.
        """
        self.directory = directory
        self.partitioning_grid = Grid.from_file(directory / partitioning_file)
        self.charge_grid = Grid.from_file(directory / charge_file)
        # partitioning = PartitioningToolkit(partitioning_grid).get_partitioning()
    
    def run_badelf(self):
        # find electrides if desired
        # run zero-flux and print atoms
        # Assign voxels from zero-flux (create method in voxel assignment)
        # get partitioning if not already there
        # assign voxels from voronoi
        # return results (or set them?)
        pass
    
    def run_voronelf(self):
        # find electrides if desired
        # get partitioning
        # regrid assignment
        # assign voxels from voronoi
        # return results
        pass
    
    def run_zero_flux(self):
        # find electrides if desired
        # run zero-flux
        # read in results
        # return resuls
        pass
