# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

from simmate.engine import S3Workflow, Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.utilities import (
    check_required_files,
    get_density_file_empty,
)

from simmate.apps.warrenapp.workflows.population_analysis.badelf_alg_v0_4_0 import (
    PopulationAnalysis__Warren__BadelfIonicRadii,
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
class PopulationAnalysis__Warren__BadelfInit(S3Workflow):
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
    use_previous_directory = ["CHGCAR", "ELFCAR", "POSCAR"]

# Workflow for running a BadELF analysis that uses the original gradient method
# described by Bader and utilized by Savin et al. Run assuming dummy atoms have
# been placed
class PopulationAnalysis__Warren__BadelfGradientEmpty(S3Workflow):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR.
    """

    command = "bader CHGCAR_empty -ref ELFCAR_empty > bader.out"
    required_files = ["CHGCAR_empty", "ELFCAR_empty"]
    use_database = False


# Same as above, but not assuming dummy atoms have been placed.
class PopulationAnalysis__Warren__BadelfGradient(S3Workflow):
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
class PopulationAnalysis__Warren__GetAtomChgcar(S3Workflow):
    """
    This workflow runs the Henkleman groups bader algorithm, partitioning based
    on the ELFCAR, and generates CHGCAR like files for each atom in the system
    """

    required_files = ["CHGCAR_empty", "ELFCAR_empty"]
    use_database = False
    use_previous_directory = ["CHGCAR","ELFCAR","POSCAR","CHGCAR_empty", "ELFCAR_empty", "POSCAR_empty"]
    monitor = False

    command = "bader CHGCAR_empty -ref ELFCAR_empty -p all_atom > bader.out"


# The base workflow that all workflows that just run BadELF analysis are built
# from. If DFT is also desired, a static_energy workflow needs to be created 
# and set.
class VaspBadElfBase(Workflow):
    """
    Runs a Badelf analysis on a pre-run VASP calculation.
    This is the base workflow that all analyses that run BadELF
    are built from. If a more traditional zero-flux surface type partitioning
    is desired, the badelf_alg tag can be set as "gradient"
    """

    database_table = BadElfAnalysis

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None, # we default to the current directory
        find_empties: bool = True,
        min_charge: float = 0.45, # This is somewhat arbitrarily set
        badelf_alg: str = "voronoi",
        print_atom_voxels: bool = False,
        **kwargs,
    ):
        # Check if the user would like to search for electride electrons
        if find_empties:
            # Run Henkelman Bader code on CHGCAR -ref ELFCAR to get initial list
            # of ELF basins. This is run in a new directory, "files_w_dummies" because
            # running workflows in the same directory will eventually be depracated
            empties_directory = directory / "files_w_dummies"
            
            PopulationAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=empties_directory,
                previous_directory=directory
            ).result()
            
            # Get CHGCAR_empty, ELFCAR_empty, and POSCAR_empty files in the
            # files_w_dummies directory
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
                        electride_indices_str = f"{electride_indices_str} {index}"
            
            # Get electride basins in CHGCAR format. These will be stored in a
            # new directory, "electride_basins". If there are no electride sites
            # we don't run an s3workflow at all and instead just manually copy the
            # necessary files
            badelf_directory = directory / "badelf"
            if electride_num > 0:
                PopulationAnalysis__Warren__GetAtomChgcar.run(
                    directory=badelf_directory,
                    previous_directory=empties_directory,
                    command=f"bader CHGCAR_empty -ref ELFCAR_empty -p sel_atom {electride_indices_str}"
                ).result()
            else:
                # There are no electride sites, but we still need these files in
                # the final BadELF workflow so we manually copy them.
                try:
                    Path(directory / "badelf").mkdir()
                except:
                    pass
                for file in ["CHGCAR","ELFCAR","POSCAR","CHGCAR_empty", "ELFCAR_empty", "POSCAR_empty"]:
                    shutil.copy(empties_directory/file, badelf_directory)
            
            if badelf_alg == "voronoi":
                # Run Warren lab BadELF algorithm and get desired data to save
                # to the dataframe
                results = PopulationAnalysis__Warren__BadelfIonicRadii.run(
                    directory=badelf_directory,
                    print_atom_voxels=print_atom_voxels).result()
                
            elif badelf_alg == "gradient":
                # Run bader version of BadELF algorithm
                PopulationAnalysis__Warren__BadelfGradientEmpty.run(
                    directory=badelf_directory,
                )
                # get the desired data that will be saved to the dataframe
                dataframe, extra_data = ACF(directory)
                results = {
                    "oxidation_states": list(dataframe.oxidation_state.values),
                    "charges": list(dataframe.charge.values),
                    "min_dists": list(dataframe.min_dist.values),
                    "atomic_volumes": list(dataframe.atomic_vol.values),
                    "element_list": list(dataframe.element.values),
                    "nelectrides": electride_num,
                    "algorithm": badelf_alg
                    **extra_data,
                }
                
            else:
                raise Exception(
                    """The badelf_alg setting you chose does not exist. Please select
                      either 'voronoi' or 'gradient'.
                      """
                )
            return results
        #!!! Need to make sure this happens in directory called "badelf" and that
        # everything is saved the same way as above.
        # if finding electride sites is set to false by the user, switch to the
        # following workflow
        else:
            if badelf_alg == "voronoi":
                # Run badelf on initial output
                PopulationAnalysis__Warren__BadelfIonicRadii.run(
                    directory=directory,
                    empty_structure_file="POSCAR",
                    partition_file="ELFCAR",
                    charge_file="CHGCAR",
                ).result()
            elif badelf_alg == "gradient":
                # Run bader version of BadELF algorithm
                PopulationAnalysis__Warren__BadelfGradient.run(
                    directory=directory,
                )
            else:
                print(
                    """The badelf_alg setting you chose does not exist. Please select
                      either 'voronoi' or 'gradient'.
                      """
                )

