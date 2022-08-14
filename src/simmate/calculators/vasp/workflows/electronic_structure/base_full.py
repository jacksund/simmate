# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.workflow_engine import Workflow


class ElectronicStructureWorkflow(Workflow):
    """
    Runs a static energy calculation followed by non-SCF calculations for
    band structure and density of states.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - static-energy.vasp.matproj
        - band-structure.vasp.matproj
        - density-of-states.vasp.matproj

    Note, these calculations are done using PBE, which is known to underestimate
    band gaps. For higher quality electronic structure calculations, you should
    use HSE instead.
    """

    use_database = False

    static_energy_workflow: Workflow = None
    band_structure_workflow: Workflow = None
    density_of_states_workflow: Workflow = None

    @classmethod
    def run_config(
        cls,
        structure,
        command: str = None,
        source: str = None,
        directory: Path = None,
        copy_previous_directory: str = False,
        **kwargs,
    ):

        static_result = cls.static_energy_workflow.run(
            structure=structure,
            command=command,
            directory=directory / cls.static_energy_workflow.name_full,
            source=source,
            # For band-structures, unit cells should be in the standardized format
            pre_standardize_structure=True,
        ).result()  # block until complete

        dos_state = cls.density_of_states_workflow.run(
            structure={
                "database_table": cls.static_energy_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=command,
            directory=directory / cls.density_of_states_workflow.name_full,
            copy_previous_directory=True,
        )

        bs_state = cls.band_structure_workflow.run(
            structure={
                "database_table": cls.static_energy_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=command,
            directory=directory / cls.band_structure_workflow.name_full,
            copy_previous_directory=True,
        )

        # block until complete
        dos_state.result()
        bs_state.result()

        # TODO:
        # workup dos_state.result() and bs_state.result() into single figure
