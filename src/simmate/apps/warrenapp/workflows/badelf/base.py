# -*- coding: utf-8 -*-

import shutil
from pathlib import Path
import warnings

from simmate.engine import S3Workflow, Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.utilities import (
    check_required_files,
    get_density_file_empty,
)

from simmate.apps.warrenapp.workflows.badelf.badelf_alg_v0_4_0 import (
    BadElfAnalysis__Warren__BadelfIonicRadii,
)
from simmate.apps.warrenapp.models import BadElfAnalysis
from simmate.apps.warrenapp.badelf_tools.acf import ACF

# This file contains classes for performing Bader and BadELF. Parts of the code
# are based off of the Henkelman groups algorithm for Bader analysis:
# (http://theory.cm.utexas.edu/henkelman/code/bader/).
# Some workflows in this file purposefully do not use a database as they are
# part of a larger process that doesn't need to be recorded.
# All of the earlier workflows are building blocks for VaspBadelfBaderBase which
# is the workflow that all the other BadELF analysis workflows are built from.


# Workflow for running a badelf analysis to create a BCF.dat file that will
# be used to find electride sites before running further bader or badelf
# analyses.
class BadElfAnalysis__Warren__BadelfInit(S3Workflow):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR. This workflow is intended to be run before other
    Bader or Badelf workflows with the intention of creating the BCF.dat file
    needed to find electride sites.
    """

    command = "bader CHGCAR -ref ELFCAR > bader.out"
    monitor = False
    required_files = ["CHGCAR", "ELFCAR"]
    use_database = False
    use_previous_directory = ["CHGCAR", "ELFCAR", "POSCAR", "POTCAR"]

# Workflow for running a BadELF analysis that uses the original zero-flux method
# described by Bader and utilized by Savin et al. Run assuming dummy atoms have
# been placed
class BadElfAnalysis__Warren__BadelfGradientEmpty(S3Workflow):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR.
    """

    command = "bader CHGCAR_empty -ref ELFCAR_empty > bader.out"
    required_files = ["CHGCAR_empty", "ELFCAR_empty"]
    use_database = False


# Same as above, but not assuming dummy atoms have been placed.
class BadElfAnalysis__Warren__BadelfGradient(S3Workflow):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR.
    """

    command = "bader CHGCAR -ref ELFCAR > bader.out"
    required_files = ["CHGCAR", "ELFCAR", "POSCAR"]
    use_database = False


# Workflow for running the henkelman groups algorithm and
# generating chgcar like files for each atom.
# !!!
# A future version of this workflow should only print the electride electrons
# to save space.
class BadElfAnalysis__Warren__GetAtomChgcar(S3Workflow):
    """
    This workflow runs the Henkleman groups bader algorithm, partitioning based
    on the ELFCAR, and generates CHGCAR like files for each atom in the system
    """

    required_files = ["CHGCAR_empty", "ELFCAR_empty"]
    use_database = False
    use_previous_directory = ["CHGCAR","ELFCAR","POSCAR", "POTCAR","CHGCAR_empty", "ELFCAR_empty", "POSCAR_empty"]
    monitor = False

    command = "bader CHGCAR_empty -ref ELFCAR_empty -p all_atom > bader.out"


# The base workflow that all workflows that just run BadELF analysis are built
# from. If DFT is also desired, a static_energy workflow needs to be created 
# and set.
class BadElfBase(Workflow):
    """
    Runs a Badelf analysis on a pre-run VASP calculation.
    This is the base workflow that all analyses that run BadELF
    are built from.
    """

    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None, # we default to the current directory
        find_empties: bool = True,
        min_charge: float = 0.45, # This is somewhat arbitrarily set
        algorithm: str = "badelf",
        print_atom_voxels: bool = False,
        **kwargs,
    ):
        # Check if the user would like to search for electride electrons
        if find_empties:
            # Run Henkelman Bader code on CHGCAR -ref ELFCAR to get initial list
            # of ELF basins. This is run in a new directory, "files_w_dummies" because
            # running workflows in the same directory will eventually be depracated
            empties_directory = directory / "files_w_dummies"
            
            BadElfAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=empties_directory,
                previous_directory=directory
            ).result()
            
            # Get CHGCAR_empty, ELFCAR_empty, and POSCAR_empty files in the
            # files_w_dummies directory. We also suppress warnings from pymatgen
            # that we know exist but may confuse the user
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                get_density_file_empty(
                    directory=empties_directory,
                    structure=structure,
                    analysis_type="badelf",
                    min_charge=min_charge,
                )
            
            # get indices for electrides in new empty structure. These are stored
            # as a string because we are going to use them to run a command
            # in a specific format for the Henkelman group's code
            empty_structure = Structure.from_file(directory / empties_directory / "POSCAR_empty")
            electride_num = 0
            electride_indices_str = ""
            for index, element in enumerate(empty_structure.atomic_numbers):
                    if element == 2:
                        electride_num += 1
                        electride_indices_str = f"{electride_indices_str} {index+1}"
            
            # Get electride basins in CHGCAR format. These will be stored in a
            # new directory, "electride_basins". If there are no electride sites
            # we don't run an s3workflow at all and instead just manually copy the
            # necessary files
            badelf_directory = directory / "badelf"
            if electride_num > 0:
                BadElfAnalysis__Warren__GetAtomChgcar.run(
                    directory=badelf_directory,
                    previous_directory=empties_directory,
                    command=f"bader CHGCAR_empty -ref ELFCAR_empty -p sel_atom {electride_indices_str} > bader.out"
                ).result()
            else:
                # There are no electride sites, but we still need these files in
                # the final BadELF workflow so we manually copy them.
                try:
                    Path(directory / "badelf").mkdir()
                except:
                    pass
                for file in ["CHGCAR","ELFCAR","POSCAR", "POTCAR","CHGCAR_empty", "ELFCAR_empty", "POSCAR_empty"]:
                    shutil.copy(empties_directory/file, badelf_directory)
            
            if algorithm == "badelf":
                # Run Warren lab BadELF algorithm and get desired data to save
                # to the dataframe
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    print_atom_voxels=print_atom_voxels).result()
                
            elif algorithm == "zero-flux":
                # Run bader version of BadELF algorithm
                BadElfAnalysis__Warren__BadelfGradientEmpty.run(
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
                      either 'badelf' or 'zero-flux'.
                      """
                )
            return results
        #!!! Need to make sure this happens in directory called "badelf" and that
        # everything is saved the same way as above.
        # if finding electride sites is set to false by the user, switch to the
        # following workflow
        else:
            # We aren't searching for electride sites, but we still need our
            # results to be moved to a badelf directory to be consistent with
            # the method above.
            badelf_directory = directory / "badelf"
            try:
                Path(badelf_directory).mkdir()
            except:
                pass
            for file in ["CHGCAR","ELFCAR","POSCAR", "POTCAR"]:
                shutil.copy(directory/file, badelf_directory)
            
            # check which algorithm was requested
            if algorithm == "badelf":
                # Run badelf on vasp output
                results = BadElfAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    empty_structure_file="POSCAR",
                    partition_file="ELFCAR",
                    empty_partition_file="ELFCAR",
                    charge_file="CHGCAR",
                ).result()
            elif algorithm == "zero-flux":
                # Run zero-flux version of algorithm
                BadElfAnalysis__Warren__BadelfGradient.run(
                    directory=badelf_directory,
                )
                dataframe, extra_data = ACF(badelf_directory)
                # we didn't search for electrides so the number will automatically
                # be 0
                electride_num = 0
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
                      either 'badelf' or 'zero-flux'.
                      """
                )
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
        find_empties: bool = True,
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
            find_empties=find_empties,
            min_charge=min_charge,
            algorithm=algorithm,
            print_atom_voxels=print_atom_voxels,
            # copy_previous_directory=True,
        ).result()