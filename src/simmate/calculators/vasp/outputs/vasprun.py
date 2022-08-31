# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from pymatgen.io.vasp.outputs import Vasprun as VasprunPymatgen


class Vasprun(VasprunPymatgen):
    @classmethod
    def from_directory(cls, directory: Path):

        vasprun_filename = directory / "vasprun.xml"

        # load the xml file and all of the vasprun data
        try:
            vasprun = cls(
                filename=vasprun_filename,
                exception_on_bad_xml=True,
            )
        except:
            logging.warning(
                "XML is malformed. This typically means there's an error with your"
                " calculation that wasn't caught by your ErrorHandlers. We try"
                " salvaging data here though."
            )
            vasprun = cls(
                filename=vasprun_filename,
                exception_on_bad_xml=False,
            )
            vasprun.final_structure = vasprun.structures[-1]
        # This try/except is just for my really rough calculations
        # where I don't use any ErrorHandlers and still want the final structure
        # regarless of what went wrong. In the future, I should consider writing
        # a separate method for those that loads the CONTCAR and moves on.

        return vasprun
