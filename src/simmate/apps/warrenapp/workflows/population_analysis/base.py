# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

from simmate.apps.bader.workflows import PopulationAnalysis__Bader__CombineChgcars
from simmate.engine import S3Workflow, Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.utilities import (
    check_required_files,
    get_density_file_empty,
)
from simmate.apps.warrenapp.models import WarrenPopulationAnalysis
from simmate.apps.warrenapp.workflows.population_analysis.warren_badelf_v3_9 import (
    PopulationAnalysis__Warren__BadelfIonicRadii,
)

# This file contains classes for performing Bader and BadELF using the Henkelman
# groups algorithm (http://theory.cm.utexas.edu/henkelman/code/bader/).
# Some workflows in this file purposefully do not use a database as they are
# intended to be part of a larger workflow. If they are not a larger workflow,
# but do use a database, it is so the workflow will record all of the required
# data in the database. All of the earlier workflows are building blocks for
# either VaspBaderBase, VaspBadelfBase, or VaspBadelfBaderBase which are the
# workflows that all the other workflows are built from.


# Workflow for running a single bader analysis.
class PopulationAnalysis__Warren__Bader(S3Workflow):
    required_files = ["CHGCAR_sum", "CHGCAR"]
    database_table = WarrenPopulationAnalysis

    command = "bader CHGCAR -ref CHGCAR_sum -b weight > bader.out"
    # The command to call the executable, which is typically bader. Note we
    # use the `-b weight` by default, which means we apply the weight method for
    # partitioning from of
    # [Yu and Trinkle](http://theory.cm.utexas.edu/henkelman/code/bader/download/yu11_064111.pdf).

    # This command is modified to use the `-ref` file as the reference for determining
    # zero-flux surfaces when partitioning the CHGCAR.
    """ 
    This class is used to run a standard Bader analysis using the Henkelman
    group's algorithm (http://theory.cm.utexas.edu/henkelman/code/bader/). This 
    workflow is the main BadELF workflow used when not searching or working with 
    electrides. It is not intended to be run alone, but as part of a larger workflow.
    """


# Workflow for for running a bader analysis on a material containing "empty"
# atoms. Empty atoms are usually hydrogens and are meant to represent electride
# sites.
class PopulationAnalysis__Warren__BaderEmpty(S3Workflow):
    """
    This class is used to run a bader analysis when searching for or working
    with electrides. It checks if the required files with empty atoms are
    present or creates them, then runs the standard Bader analysis.
    """

    required_files = ["CHGCAR_sum_empty", "CHGCAR_empty"]
    database_table = WarrenPopulationAnalysis
    command = "bader CHGCAR_empty -ref CHGCAR_sum_empty > bader.out"

    @staticmethod
    def setup(directory, min_charge, analysis_type="bader", **kwargs):
        required_files = ["CHGCAR_sum_empty", "CHGCAR_empty", "POSCAR"]
        # Set the structure for this run
        structure = Structure.from_file(directory / "POSCAR")
        # Parse the BCF.dat file for possible electride sites and create CHGCAR_empty
        # and CHGCAR_sum_empty if found
        try:
            check_required_files(directory=directory, required_files=required_files)
        except:
            get_density_file_empty(
                directory=directory,
                structure=structure,
                analysis_type=analysis_type,
                min_charge=min_charge,
            )


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
    required_files = ["CHGCAR", "ELFCAR"]
    use_database = False


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
    database_table = WarrenPopulationAnalysis


# Same as above, but not assuming dummy atoms have been placed.
class PopulationAnalysis__Warren__BadelfGradient(S3Workflow):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR.
    """

    command = "bader CHGCAR -ref ELFCAR > bader.out"
    required_files = ["CHGCAR", "ELFCAR"]
    database_table = WarrenPopulationAnalysis


# Workflow for running the henkelman groups algorithm and
# generating chgcar like files for each atom.
class PopulationAnalysis__Warren__GetAtomChgcar(S3Workflow):
    """
    This workflow runs the Henkleman groups bader algorithm, partitioning based
    on the ELFCAR, and generates CHGCAR like files for each atom in the system
    """

    required_files = ["CHGCAR_empty", "ELFCAR_empty"]
    use_database = False

    command = "bader CHGCAR_empty -ref ELFCAR_empty -p all_atom > bader.out"

    @staticmethod
    def setup(directory, min_charge, analysis_type="bader", **kwargs):
        required_files = ["CHGCAR_empty", "ELFCAR_empty"]
        # Set the structure for this run
        structure = Structure.from_file(directory / "POSCAR")
        # Parse the BCF.dat file for possible electride sites and create CHGCAR_empty
        # and CHGCAR_sum_empty if found
        try:
            check_required_files(directory=directory, required_files=required_files)
        except:
            get_density_file_empty(
                directory=directory,
                structure=structure,
                analysis_type=analysis_type,
                min_charge=min_charge,
            )


# The base workflow that all workflows that just run bader analysis are built
# from. For these a static_energy workflow needs to be created and set. The
# workflow can take in an extra parameter, find_empties, which can be set to
# true when searching for electrides is desired.
class VaspBaderBase(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Bader analysis on the resulting charge density. This
    is the base workflow that all of the Bader workflows are built out from.
    """

    static_energy_prebader: Workflow = None  # This must be defined in inheriting class
    static_energy_prebadelf: Workflow = None
    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        find_empties: bool = True,
        directory: Path = None,
        min_charge: float = 0.15,
        **kwargs,
    ):
        if find_empties:
            # Run static energy calculation if not already done
            if cls.static_energy_prebadelf is not None:
                prebader_result = cls.static_energy_prebadelf.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()
            # Run badelf on initial file output
            PopulationAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=directory,
            ).result()
            # Combine AECCAR0 and AECCAR2
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # The previous directory (where AECCAR0 and AECCAR2 are located) is
            # the same as the new directory where CHGCAR_sum will be. Jack has
            # warned that this may be disallowed in the future so it may need
            # fixing.
            PopulationAnalysis__Bader__CombineChgcars.run(
                directory=directory,
                previous_director=directory,
            ).result()
            # Find electride sites, place empty atoms, and run bader
            PopulationAnalysis__Warren__BaderEmpty.run(
                structure=structure,
                directory=directory,
                min_charge=min_charge,
            )

        else:
            if cls.static_energy_prebader is not None:
                prebader_result = cls.static_energy_prebader.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()

            # Setup chargecars for the bader analysis and wait until complete
            PopulationAnalysis__Bader__CombineChgcars.run(
                directory=directory,
                previous_director=directory,
            ).result()

            # Bader only adds files and doesn't overwrite any, so I just run it
            # in the original directory. I may switch to copying over to a new
            # directory in the future though.
            PopulationAnalysis__Warren__Bader.run(
                directory=directory,
            ).result()


# Similar to the above workflow, this workflow is the base off of which all
# workflows that just run badelf are built. It also takes in the find_empties
# parameter.
class VaspBadElfBase(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning. This is the base workflow that all of the
    BadELF workflows are built out from.
    """

    static_energy_prebadelf: Workflow = None  # This must be defined in inheriting class
    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        find_empties: bool = False,
        directory: Path = None,
        min_charge: float = 0.15,
        badelf_alg: str = "voronoi",
        **kwargs,
    ):
        if find_empties:
            # Run static_energy calculation if not already done
            if cls.static_energy_prebadelf is not None:
                prebadelf_result = cls.static_energy_prebadelf.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()
            # Run badelf on initial output
            PopulationAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=directory,
            ).result()
            # Find electride sites, place empty atoms, and generate chgcar
            # like files for each atomic site
            PopulationAnalysis__Warren__GetAtomChgcar.run(
                directory=directory,
                analysis_type="badelf",
                min_charge=min_charge,
            )
            if badelf_alg == "voronoi":
                # Run Warren lab version of BadELF algorithm
                PopulationAnalysis__Warren__BadelfIonicRadii.run(
                    directory=directory,
                )
            elif badelf_alg == "gradient":
                PopulationAnalysis__Warren__BadelfGradientEmpty.run(
                    directory=directory,
                )
            else:
                print(
                    """The badelf_alg setting you chose does not exist. Please select
                      either 'voronoi' or 'gradient'.
                      """
                )
        else:
            if cls.static_energy_prebadelf is not None:
                prebadelf_result = cls.static_energy_prebadelf.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()

            # Bader only adds files and doesn't overwrite any, so I just run it
            # in the original directory. I may switch to copying over to a new
            # directory in the future though.
            # We don't need to generate empty atom files because we're not looking
            # for electride sites here.
            if badelf_alg == "voronoi":
                PopulationAnalysis__Warren__BadelfIonicRadii.run(
                    directory=directory,
                    empty_structure_file="POSCAR",
                    partition_file="ELFCAR",
                    charge_file="CHGCAR",
                ).result()
            elif badelf_alg == "gradient":
                PopulationAnalysis__Warren__BadelfGradient.run(
                    directory=directory,
                )
            else:
                print(
                    """The badelf_alg setting you chose does not exist. Please select
                      either 'voronoi' or 'gradient'.
                      """
                )


class VaspBaderBadElfBase(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    This is the base workflow that all analyses that run both Bader and BadELF
    are built from.
    """

    static_energy_prebadelf: Workflow = None  # Must be defined in inheriting class
    use_database = False

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        find_empties: bool = True,
        directory: Path = None,
        min_charge: float = 0.15,
        badelf_alg: str = "voronoi",
        **kwargs,
    ):
        # Define files that will be copied into badelf and bader subdirectories
        badelf_files = ["ACF.dat", "simmate_population_summary.csv"]
        bader_files = [
            "ACF.dat",
            "BCF.dat",
            "AVF.dat",
            "simmate_population_summary.csv",
        ]
        if find_empties:
            # Run static_energy calculation if not already run
            if cls.static_energy_prebadelf is not None:
                prebadelf_result = cls.static_energy_prebadelf.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()
            # Combine AECCAR0 and AECCAR2 for bader later in workflow
            PopulationAnalysis__Bader__CombineChgcars.run(
                directory=directory,
                previous_director=directory,
            ).result()
            # Run badelf on initial output
            PopulationAnalysis__Warren__BadelfInit.run(
                structure=structure,
                directory=directory,
            ).result()
            # Find electride sites, place empty atoms, and get atom charges
            # in CHGCAR format
            PopulationAnalysis__Warren__GetAtomChgcar.run(
                directory=directory,
                analysis_type="both",
                min_charge=min_charge,
            ).result()
            if badelf_alg == "voronoi":
                # Run Warren lab BadELF algorithm
                PopulationAnalysis__Warren__BadelfIonicRadii.run(directory=directory)
            elif badelf_alg == "gradient":
                # Run bader version of BadELF algorithm
                PopulationAnalysis__Warren__BadelfGradientEmpty.run(
                    directory=directory,
                )
            else:
                print(
                    """The badelf_alg setting you chose does not exist. Please select
                      either 'voronoi' or 'gradient'.
                      """
                )
            # Create directories for badelf and bader results so that they
            # don't get overwritten
            try:
                Path(directory / "badelf").mkdir()
                Path(directory / "bader").mkdir()
            except:
                pass
            # Copy badelf results into badelf
            for file in badelf_files:
                shutil.copy(directory / file, directory / "badelf")
            # shutil.copy(
            #     directory / "simmate_population_summary.csv", directory / "badelf"
            # )
            # Run bader analysis
            PopulationAnalysis__Warren__BaderEmpty.run(
                structure=structure,
                directory=directory,
                min_charge=min_charge,
            ).result()
            # Copy bader results into bader
            for file in bader_files:
                shutil.copy(directory / file, directory / "bader")
        else:
            if cls.static_energy_prebadelf is not None:
                prebadelf_result = cls.static_energy_prebadelf.run(
                    structure=structure,
                    command=command,
                    source=source,
                    directory=directory,
                ).result()

            # Setup chargecars for the bader analysis and wait until complete
            PopulationAnalysis__Bader__CombineChgcars.run(
                directory=directory,
                previous_director=directory,
            ).result()
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
            # Create directories for badelf and bader results
            try:
                Path(directory / "badelf").mkdir()
                Path(directory / "bader").mkdir()
            except:
                pass
            # Copy badelf files
            for file in badelf_files:
                shutil.copy(directory / file, directory / "badelf")
            # shutil.copy(
            #     directory / "simmate_population_summary.csv", directory / "badelf"
            # )
            # Run bader
            PopulationAnalysis__Warren__Bader.run(
                directory=directory,
            ).result()
            # Copy bader files
            for file in bader_files:
                shutil.copy(directory / file, directory / "bader")


# We want to define the settings that will be used when updating static energy
# workflows for prebader or prebadelf DFT calculations. We do that here so
# that we don't need to do it in every inheriting class.
prebader_incar_settings = dict(
    NGXF__density_a=40,
    NGYF__density_b=40,
    NGZF__density_c=40,
    LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
)
prebadelf_incar_settings = dict(
    NGX__density_a=40,  # Note that these set the FFT grid while the pre-Bader task sets the
    NGY__density_b=40,  # fine FFT grid (e.g. useds NGX instead of NGXF)
    NGZ__density_c=40,
    LELF=True,  # Writes the ELFCAR
    NPAR=1,  # Must be set if LELF is set
    PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
    LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
)
