# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
import warnings

from simmate.engine import S3Workflow, Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.utilities import (
    get_density_file_empty,
    convert_atom_chgcar_to_elfcar,
)

from simmate.apps.warrenapp.workflows.badelf.badelf_alg_v0_4_0 import (
    BadElfAnalysis__Warren__BadelfIonicRadii,
)
from simmate.apps.warrenapp.workflows.badelf.topology_alg_v0_1_0 import (
    get_electride_dimensionality    
)

from simmate.apps.warrenapp.badelf_tools.acf import ACF

# This file contains workflows for performing Bader and BadELF. Parts of the code
# use the Henkelman groups algorithm for Bader analysis:
# (http://theory.cm.utexas.edu/henkelman/code/bader/).

# Some workflows in this file purposefully do not use a database as they are
# part of a larger process that doesn't need to be recorded.
# All of the earlier workflows are building blocks for VaspBadelfBaderBase which
# is the workflow that all the other BadELF analysis workflows are built from.

# The only differences between the following S3Workflows is that they have different
# required files and some use the previous directory and need specific files.
# The command can be changed when the workflow is called for a run, so it is
# not strictly necessary that this be set if their only use is in the base
# BadELF workflow below.


class BadElfAnalysis__Warren__BadelfZeroFlux(S3Workflow):
    """
    Runs charge analysis where the ELFCAR is used as the partitioning reference. 
    This corresponds to the Zero-Flux bader method.
    """
    command = "bader CHGCAR -ref ELFCAR > bader.out"
    required_files = ["CHGCAR", "ELFCAR", "POSCAR"]
    monitor = False #There is no monitor for the Henkelman's code built out yet
    use_database = False

class BadElfAnalysis__Warren__BadelfZeroFluxEmpty(BadElfAnalysis__Warren__BadelfZeroFlux):
    """
    Runs the same analysis as the BadelfZeroFlux workflow above. However, it
    uses files with _empty at the end which indicate that the algorithm searched
    for electrides.
    """
    command = "bader CHGCAR_empty -ref ELFCAR_empty > bader.out"
    required_files = ["CHGCAR_empty", "ELFCAR_empty"]

class BadElfAnalysis__Warren__BadelfInit(BadElfAnalysis__Warren__BadelfZeroFlux):
    """
    Runs the same analysis as the BadelfZeroFlux workflow above, but copies the
    necessary files from a previous directory. This workflow is run at the beginning
    of the base BadELF workflow to create the BCF.dat file that is used to
    automatically find electride sites.
    """
    use_previous_directory = ["CHGCAR", "ELFCAR", "POSCAR", "POTCAR"]


class BadElfBase(Workflow):
    """
    Controls a Badelf analysis on a pre-ran VASP calculation.
    This is the base workflow that all analyses that run BadELF
    are built from.
    """

    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        source: dict = None,
        directory: Path = None,
        find_electrides: bool = True,
        min_charge: float = 0.45, # This is somewhat arbitrarily set
        algorithm: str = "badelf",
        print_atom_voxels: bool = False,
        **kwargs,
    ):
        #!!! Add method to set ELFCAR grid to the same size as CHGCAR grid if
        # they are not. This would solve any issues with users not using the
        # correct vasp settings.
        #######################################################################
        # This section of the workflow finds electride sites (if requested)   #
        #######################################################################
        if find_electrides:
            # Run Henkelman Bader code on CHGCAR -ref ELFCAR to get initial list
            # of ELF basins. This is run in a new directory, "files_w_dummies" because
            # running workflows in the same directory will eventually be depracated
            empties_directory = directory / "files_w_electrides"
            
            BadElfAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=empties_directory,
                previous_directory=directory,
            ).result()
            
            # Get CHGCAR_empty, ELFCAR_empty, and POSCAR_empty files in the
            # files_w_dummies directory. This function also returns a structure
            # with empty 'dummy' atoms if electrides are found as well as the
            # number of electride sites. Otherwise it returns None, None.
            # We also suppress warnings from pymatgen that we know exist but may 
            # confuse the user.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                empty_structure, electride_num = get_density_file_empty(
                    directory=empties_directory,
                    structure=structure,
                    analysis_type="badelf",
                    min_charge=min_charge,
                )
            
            if empty_structure is not None:
                # get indices for electrides in new empty structure. These are stored
                # as a string because we are going to use them to run a command
                # in a specific format for the Henkelman group's code
                electride_indices_str = ""
                for index, element in enumerate(empty_structure.atomic_numbers):
                        if element == 2:
                            electride_indices_str = f"{electride_indices_str} {index+1}"
        
        # If finding electride sites wasn't requested, we set the number of electrides
        # to zero.
        else: electride_num = 0
        
        #######################################################################
        # This section of the workflow creates a badelf folder and copies the #
        # appropriate files into it.                                          #
        #######################################################################
        
        # Create variable for if electrides are present and make lists of the
        # required files.
        if electride_num > 0:
            electrides_present = True
            required_files = ["CHGCAR","ELFCAR","POSCAR", "POTCAR","CHGCAR_empty", "ELFCAR_empty", "POSCAR_empty"]
        else:
            required_files = ["CHGCAR","ELFCAR","POSCAR", "POTCAR"]
            empties_directory = directory
            electrides_present = False
        
        # Create a directory to run our badelf calculation in. The try/except is
        # in case the directory already exists from a previous run.
        badelf_directory = directory / "badelf"
        if not badelf_directory.exists():
            Path(badelf_directory).mkdir()    
        # Copy required files over to our badelf directory
        for file in required_files:
            shutil.copy(empties_directory/file, badelf_directory)
        
        
        #######################################################################
        # This section of the workflow checks which algorithm was selected and#
        # runs the algorithm with the appropriate settings (depending on if   #
        # there are any electride sites.)                                     #
        #######################################################################
        if algorithm == "badelf":
            if electrides_present:
                         
                # Get electride basins in CHGCAR format. These will be stored in a
                # new directory, "electride_basins". If there are no electride sites
                # we don't run an s3workflow at all and instead just manually copy the
                # necessary files
                BadElfAnalysis__Warren__BadelfZeroFluxEmpty.run(
                        directory=badelf_directory,
                        command=f"bader CHGCAR_empty -ref ELFCAR_empty -p sel_atom {electride_indices_str} > bader.out"
                    ).result()
                
                # Run Warren lab BadELF algorithm and get desired data to save
                # to the dataframe
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    print_atom_voxels=print_atom_voxels).result()
            else:
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    empty_structure_file="POSCAR",
                    partition_file="ELFCAR",
                    empty_partition_file="ELFCAR",
                ).result()
            
            
        elif algorithm == "voronelf":
            if electrides_present:
                # Run Warren lab BadELF algorithm and get desired data to save
                # to the dataframe
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    print_atom_voxels=print_atom_voxels,
                    algorithm=algorithm,
                    structure_file="POSCAR_empty",
                    partition_file="ELFCAR_empty",
                    charge_file="CHGCAR_empty"
                    ).result()
            else:
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    print_atom_voxels=print_atom_voxels,
                    algorithm=algorithm,
                    empty_structure_file="POSCAR",
                    empty_partition_file="ELFCAR",
                    ).result()
                
        elif algorithm == "zero-flux":
            # Run the appropriate zero-flux algorithm depending on if we need
            # empty files or not
            if electrides_present:
                BadElfAnalysis__Warren__BadelfZeroFluxEmpty.run(
                    directory=badelf_directory,
                    command=f"bader CHGCAR_empty -ref ELFCAR_empty -p sum_atom {electride_indices_str} > bader.out",
                )
                # We need a file named ELFCAR_e for the topology function to run.
                # We run a function here that converts from a BvAt_sum.dat chgcar
                # type file to the required ELFCAR type file
                convert_atom_chgcar_to_elfcar(badelf_directory)
            
            else:
                BadElfAnalysis__Warren__BadelfZeroFlux.run(
                    directory=badelf_directory,
                )
            
            # get the desired data that will be saved to the dataframe
            dataframe, extra_data = ACF(badelf_directory)
            results = {
                "oxidation_states": list(dataframe.oxidation_state.values),
                "charges": list(dataframe.charge.values),
                "min_dists": list(dataframe.min_dist.values),
                "atomic_volumes": list(dataframe.atomic_vol.values),
                "element_list": list(dataframe.element.values),
                "nelectrides": electride_num,
                "algorithm": algorithm,
                **extra_data,
            }
           
        else:
            raise Exception(
                """The algorithm setting you chose does not exist. Please select
                  either 'badelf', 'voronelf', or 'zero-flux'.
                  """
            )
            
        #######################################################################
        # This section of the workflow determines the dimensionality of the   #
        # electride network (if it exists) and adds it to the workflow results#
        #######################################################################
        if electrides_present:
            dimensionality = get_electride_dimensionality(
                directory = badelf_directory,
                empty_structure = empty_structure,
                )
            results["electride_dim"] = dimensionality
        
        return results


class VaspBadElfBase(Workflow):
    """
    Runs a VASP DFT calculation followed by a BadELF analysis. This is the base 
    workflow that all analyses that run DFT and BadELF are built from.
    """

    use_database = False
    static_energy_workflow = None #This should be defined in the inheriting class
    badelf_workflow = None # This should be defined in the inheriting class
                           # usually as the BadElfAnalyisis__warrenapp__badelf workflow

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None, # we default to the current directory
        find_electrides: bool = True,
        min_charge: float = 0.45, # This is somewhat arbitrarily set
        algorithm: str = "badelf",
        print_atom_voxels: bool = False,
        **kwargs,
    ):
        
        # Run the dft calculation. This workflow should be set as something
        # that already saves to a database table.
        static_energy_directory = directory / "static_energy"
        static_energy_result = cls.static_energy_workflow.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_energy_directory,
        ).result()

        # run the badelf analysis in the same directory as the DFT. This workflow
        # should be set to something that already saves to a database table.

        badelf_result = cls.badelf_workflow.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_energy_directory,
            find_electrides=find_electrides,
            min_charge=min_charge,
            algorithm=algorithm,
            print_atom_voxels=print_atom_voxels,
            # copy_previous_directory=True,
        ).result()