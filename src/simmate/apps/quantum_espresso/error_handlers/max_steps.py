# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.quantum_espresso.inputs import PwscfInput
from simmate.apps.quantum_espresso.outputs import PwscfXml
from simmate.workflows.core.error_handler import ErrorHandler


class MaxSteps(ErrorHandler):
    """
    Checks if a geometry relaxation failed to converge because the maximum 
    number of ionic steps was reached.
    
    The fix is simply to read the final coordinates from the aborted calculation 
    and restart the optimization from that geometry.
    """

    is_monitor = False
    filename_to_check = "pw-scf.out"
    possible_error_messages = ["The maximum number of steps has been reached."]

    def correct(self, directory: Path) -> str:
        # Load the latest structure from the xml output
        xml_file = directory / "pwscf.xml"
        xml_reader = PwscfXml.from_file(xml_file)
        latest_structure = xml_reader.final_structure

        # Load the original input file
        in_file = directory / "pwscf.in"
        pwscf_input = PwscfInput.from_file(in_file)

        # Update the structure with the latest one
        pwscf_input.structure = latest_structure
        pwscf_input.to_file(in_file)

        return "restarted calculation from latest coordinates"
