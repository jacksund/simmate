# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import load_input_and_register


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

    static_energy_workflow: Workflow = None
    band_structure_workflow: Workflow = None
    density_of_states_workflow: Workflow = None

    @classmethod
    def run_config(
        cls,
        structure,
        command: str = None,
        source: str = None,
        directory: str = None,
        copy_previous_directory: str = False,
    ):

        parameters_cleaned = load_input_and_register(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
            copy_previous_directory=copy_previous_directory,
            register_run=False,
        )

        static_result = cls.static_energy_workflow.run(
            structure=parameters_cleaned["structure"],
            command=parameters_cleaned.get("command"),
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + cls.static_energy_workflow.name_full,
            source=parameters_cleaned["source"],
            # For band-structures, unit cells should be in the standardized format
            pre_standardize_structure=True,
        ).result()  # block until complete

        dos_state = cls.density_of_states_workflow.run(
            structure={
                "database_table": cls.static_energy_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=parameters_cleaned.get("command"),
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + cls.density_of_states_workflow.name_full,
            copy_previous_directory=True,
        )

        bs_state = cls.band_structure_workflow.run(
            structure={
                "database_table": cls.static_energy_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=parameters_cleaned.get("command"),
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + cls.band_structure_workflow.name_full,
            copy_previous_directory=True,
        )

        # block until complete
        dos_state.result()
        bs_state.result()

        # TODO:
        # workup dos_state.result() and bs_state.result() into single figure
