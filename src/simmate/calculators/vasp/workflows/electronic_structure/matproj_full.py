# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import load_input_and_register

from simmate.calculators.vasp.workflows.static_energy.Matproj import (
    StaticEnergy__Vasp__Matproj as static_workflow,
)
from simmate.calculators.vasp.workflows.electronic_structure.Matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates as dos_workflow,
)
from simmate.calculators.vasp.workflows.electronic_structure.Matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure as bandstruct_workflow,
)


class ElectronicStructure__Vasp__MatprojFull(Workflow):
    """
    Runs a static energy calculation followed by non-SCF calculations for
    band structure and density of states.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - static-energy.vasp.Matproj
        - band-structure.vasp.Matproj
        - density-of-states.vasp.Matproj

    Note, these calculations are done using PBE, which is known to underestimate
    band gaps. For higher quality electronic structure calculations, you should
    use HSE instead.
    """

    description_doc_short = "runs DOS and BS at Materials Project settings"

    # table not implemented yet. This is a placeholder
    database_table = bandstruct_workflow.database_table

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
        ).result()

        static_result = static_workflow.run(
            structure=parameters_cleaned["structure"],
            command=parameters_cleaned["command"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + static_workflow.name,
            source=parameters_cleaned["source"],
        ).result()  # block until complete

        dos_state = dos_workflow.run(
            structure={
                "database_table": static_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=parameters_cleaned["command"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + dos_workflow.name_full,
            copy_previous_directory=True,
            source=None,  # default to structure dict above
        )

        bs_state = bandstruct_workflow.run(
            structure={
                "database_table": static_workflow.database_table.__name__,
                "directory": static_result["directory"],
            },
            command=parameters_cleaned["command"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + dos_workflow.name_full,
            copy_previous_directory=True,
            source=None,  # default to structure dict above
        )

        # block until complete
        dos_state.result()
        bs_state.result()

        # TODO:
        # workup dos_state.result() and bs_state.result() into single figure
