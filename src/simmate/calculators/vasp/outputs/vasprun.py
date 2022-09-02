# -*- coding: utf-8 -*-

import logging
import shutil
from pathlib import Path

from pymatgen.analysis.transition_state import NEBAnalysis
from pymatgen.io.vasp.outputs import Vasprun as VasprunPymatgen


class Vasprun(VasprunPymatgen):
    @classmethod
    def from_directory(cls, directory: Path = None):

        if not directory:
            directory = Path.cwd()

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

        # set source directory for convenience elsewhere
        vasprun.directory = directory

        return vasprun

    @property
    def neb_results(self):

        directory = getattr(self, "directory", None)
        if not directory:
            raise Exception(
                "The Vasprun must have been created with the `from_directory` "
                "method in order to load neb results because it involves loading "
                "more results from files."
            )

        # Make sure there is "*.start" and "*.end" directory present. These
        # will be our start/end folders. We go through all foldernames in the
        # directory and grab the first that matches
        # BUG: For now I assume there are start/end image directories are located
        # in the working directory. These relaxation are actually ran by a
        # separate workflow, which is thus a prerequisite for this workflow.

        # assume foldernames of start and end until proven otherwise
        start_dirname = directory / "start"
        end_dirname = directory / "end"

        for name in directory.iterdir():
            if name.suffix == ".start":
                start_dirname = name
            elif name.suffix == ".end":
                end_dirname = name

        if not start_dirname.exists() or not end_dirname.exists():
            raise Exception(
                "Your NEB calculation finished (possibly successfully). However, "
                "in order to run the workup, Simmate needs the start/end point "
                "relaxations. These should be located in the same directory as "
                "the NEB run and with folder names ending  with '*.start' and"
                " '*.end' (e.g. 'image.start' and image.end' will work)"
            )

        ################
        # BUG: NEBAnalysis.from_dir is broken for all folder structures except
        # when the start/end points are in the 00 and N folders. I therefore
        # need to copy the OUTCAR from the endpoint relaxations to these folders.
        # I don't want to mess with opening a pull request with them / waiting
        # on a new release, so I make this hacky fix here
        new_start_filename = directory / "00" / "OUTCAR"
        # the end filename should be the highest number in the directory
        numbered_dirs = [d for d in directory.iterdir() if d.name.isdigit()]
        numbered_dirs.sort()
        new_end_filename = directory / numbered_dirs[-1] / "OUTCAR"
        # now copy the outcars over
        shutil.copyfile(start_dirname / "OUTCAR", new_start_filename)
        shutil.copyfile(end_dirname / "OUTCAR", new_end_filename)
        ################

        neb_results = NEBAnalysis.from_dir(
            directory,
            # BUG: see bug fix right above this
            # relaxation_dirs=[
            #     "endpoint_relaxation_start",
            #     "endpoint_relaxation_end",
            # ],
        )
        return neb_results
