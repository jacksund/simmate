# -*- coding: utf-8 -*-

"""
Runs a NEB on all unique pathways within a structure. 

The folder tree looks like...
```
simmate-task-12345/  # determined by simmate.utilities.get_directory
    ├── bulk_relaxation
    ├── bulk_static_energy
    ├── migration_hop_00
    ├── migration_hop_01
    ...
    └── migration_hop_N  # all migration_hop folders have the same structure
        ├── endpoint_relaxation_start
        ├── endpoint_relaxation_end
        ├── 01
        ├── 02
        ├── 03
        ...
        └── N  # corresponds to image number
```
"""

from pathlib import Path

from simmate.calculators.vasp.workflows.diffusion.neb_single_path_mit import (
    Diffusion__Vasp__NebSinglePathMit,
)
from simmate.calculators.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit
from simmate.calculators.vasp.workflows.static_energy.mit import StaticEnergy__Vasp__Mit
from simmate.toolkit import Structure
from simmate.toolkit.diffusion import DistinctPathFinder
from simmate.workflow_engine import Workflow


class Diffusion__Vasp__NebAllPathsMit(Workflow):
    """
    Runs a full diffusion analysis on a bulk crystal structure using NEB.

    The bulk structure will be geometry optimized and then
    `simmate.toolkit.diffusion.DistinctPathFinder` is used to find all
    symmetrically unique migration hops in the structure up until the hops
    become percolating (>0-D). For each unique hop, the workflow
    diffusion/single_path is submitted.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/mit
        - static-energy/mit
        - a mini task that identifies unique migration hops
        - (for each hop) diffusion/single-path
    """

    use_database = False
    # register_run=False,

    description_doc_short = "runs NEB for all symmetrically unique paths"

    # command list expects three subcommands:
    #   command_bulk, command_supercell, and command_neb
    #
    # I separate these out because each calculation is a very different scale.
    # For example, you may want to run the bulk relaxation on 10 cores, the
    # supercell on 50, and the NEB on 200. Even though more cores are available,
    # running smaller calculation on more cores could slow down the calc.
    # ["command_bulk", "command_supercell", "command_neb"]
    #
    #
    # If you are running this workflow via the command-line, you can run this
    # with...

    # ``` bash
    # simmate workflows run diffusion/all-paths -s example.cif -c "cmd1; cmd2; cmd3"
    # ```
    # Note, the `-c` here is very important! Here we are passing three commands
    # separated by semicolons. Each command is passed to a specific workflow call:
    #     - cmd1 --> used for bulk crystal relaxation and static energy
    #     - cmd2 --> used for endpoint supercell relaxations
    #     - cmd3 --> used for NEB
    # Thus, you can scale your resources for each step. Here's a full -c option:
    # -c "vasp_std > vasp.out; mpirun -n 12 vasp_std > vasp.out; mpirun -n 70 vasp_std > vasp.out"

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        migrating_specie: str,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        is_restart: bool = False,
        # parameters for supercell and image generation
        nimages: int = 5,
        min_atoms: int = 80,
        max_atoms: int = 240,
        min_length: float = 10,
        **kwargs,
    ):

        # Our step is to run a relaxation on the bulk structure and it uses our inputs
        # directly. The remaining one tasks pass on results.
        bulk_relax_result = Relaxation__Vasp__Mit.run(
            structure=structure,
            command=command,  # subcommands["command_bulk"]
            directory=directory / Relaxation__Vasp__Mit.name_full,
            is_restart=is_restart,
        ).result()

        # A static energy calculation on the relaxed structure. This isn't necessarily
        # required for NEB, but it takes very little time.
        bulk_static_energy_result = StaticEnergy__Vasp__Mit.run(
            structure={
                "database_table": Relaxation__Vasp__Mit.database_table.__name__,
                "directory": bulk_relax_result["directory"],
                "structure_field": "structure_final",
            },
            command=command,  # subcommands["command_bulk"]
            directory=directory / StaticEnergy__Vasp__Mit.name_full,
            is_restart=is_restart,
        ).result()

        # This step does NOT run any calculation, but instead, identifies all
        # diffusion pathways and builds the necessary database entries.
        migration_hop_ids = cls._build_diffusion_analysis(
            structure={
                "database_table": StaticEnergy__Vasp__Mit.database_table.__name__,
                "directory": bulk_static_energy_result["directory"],
            },
            migrating_specie=migrating_specie,
            directory=directory,
            vacancy_mode=True,  # assumed for now
        )

        # Run NEB single_path workflow for all these.
        for i, hop_id in enumerate(migration_hop_ids):
            state = Diffusion__Vasp__NebSinglePathMit.run(
                migration_hop={
                    "migration_hop_table": "MigrationHop",
                    "migration_hop_id": hop_id,
                },
                directory=directory
                / f"{Diffusion__Vasp__NebSinglePathMit.name_full}.{str(i).zfill(2)}",
                diffusion_analysis_id=None,
                migration_hop_id=None,
                command=command,
                # subcommands["command_supercell"]
                # + ";"
                # + subcommands["command_neb"],
                is_restart=is_restart,
                min_atoms=min_atoms,
                max_atoms=max_atoms,
                min_length=min_length,
                nimages=nimages,
            )  # we don't want to wait on results to in order to allow parallel runs

    @classmethod
    def _build_diffusion_analysis(
        cls,
        structure: Structure,
        migrating_specie: str,
        vacancy_mode: bool,
        directory: Path = None,
        **kwargs,
    ) -> list[str]:
        """
        Given a bulk crystal structure, returns all symmetrically unique pathways
        for the migrating specie (up until the path is percolating). This
        also create all relevent database entries for this struture and its
        migration hops.

        #### Parameters

        - `structure`:
            bulk crystal structure to be analyzed. Can be in any format supported
            by Structure.from_dynamic method.

        - `migrating_specie`:
            Element or ion symbol of the diffusion specie (e.g. "Li")

        - `directory`:
            where to write the CIF file visualizing all migration hops. If no
            directory is provided, it will be written in the working directory.

        - `**kwargs`:
            Any parameter normally accepted by DistinctPathFinder
        """
        if not directory:
            directory = Path("")

        ###### STEP 1: creating the toolkit objects and writing them to file

        structure_cleaned = Structure.from_dynamic(structure)

        pathfinder = DistinctPathFinder(
            structure_cleaned,
            migrating_specie,
            **kwargs,
        )
        migration_hops = pathfinder.get_paths()

        # We write all the path files so users can visualized them if needed
        filename = directory / "migration_hop_all.cif"
        pathfinder.write_all_paths(filename, nimages=10)
        for i, migration_hop in enumerate(migration_hops):
            number = str(i).zfill(2)  # converts numbers like 2 to "02"
            # the files names here will be like "migration_hop_02.cif"
            migration_hop.write_path(
                directory / f"migration_hop_{number}.cif",
                nimages=10,  # this is just for visualization
            )

        ###### STEP 2: creating the database objects and saving them to the db

        # Create the main DiffusionAnalysis object that others will link to.
        da_obj = cls.database_table.from_toolkit(
            structure=structure_cleaned,
            migrating_specie=migrating_specie,
            vacancy_mode=vacancy_mode,
        )
        da_obj.save()
        # TODO: should I search for a matching bulk structure before deciding
        # to create a new DiffusionAnalysis entry?

        # grab the linked MigrationHop class
        hop_class = da_obj.migration_hops.model

        # Now iterate through the hops and add them to the database
        hop_ids = []
        for i, hop in enumerate(migration_hops):
            hop_db = hop_class.from_toolkit(
                migration_hop=hop,
                number=i,
                diffusion_analysis_id=da_obj.id,
            )
            hop_db.save()
            hop_ids.append(hop_db.id)

        # TODO: still figuring out if toolkit vs. db objects should be returned.
        # Maybe add ids to the toolkit objects? Or dynamic DB dictionaries?
        # For now I return the MigrationHop ids -- because this let's me
        # indicate which MigrationHops should be updated later on.
        return hop_ids
