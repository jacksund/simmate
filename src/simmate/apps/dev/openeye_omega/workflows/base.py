# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.dev.openeye_omega.inputs import OmegaParm
from simmate.engine import S3Workflow
from simmate.toolkit import Molecule
from simmate.toolkit.file_converters import SmilesAdapter


class OmegaWorkflow(S3Workflow):
    required_files = ["parameters.txt", "input.smi"]
    monitor = False
    use_database = False

    command: str = "oeomega classic -param parameters.txt"
    """
    The command to call omega, which is typically oeomega. To ensure error
    handlers work properly, make sure your command has "-param parameters.txt" 
    at the end.
    """
    # TODO: add support for grabbing a user-set default from their configuration
    # TODO: add auto check for parameters.txt ending

    parameters: dict = None
    """
    This sets the default omega settings from a dictionary. This is the one thing
    you *must* set when subclassing OmegaWorkflow. An example is:
        
    ``` python
    parameters = dict(
        commentEnergy=True,
        maxConfs=10,
    )
    ```
    """

    @classmethod
    def setup(
        cls,
        directory: Path,
        molecules: list[Molecule],
        **kwargs,
    ):
        # establish filenames
        parm_filename = directory / "parameters.txt"
        input_filename = directory / "input.smi"
        output_filename = directory / "output.sdf"

        # write the parameters file
        parm_config = OmegaParm(
            in_=input_filename,
            out=output_filename,
            **cls.parameters,
        )
        parm_config.to_file(parm_filename)

        # write all molecules to an input file
        # For now, we assume that the Molecules are 2D and can be
        # written to SMILES
        SmilesAdapter.to_file_from_toolkits(molecules, input_filename)
