# -*- coding: utf-8 -*-

import os
from pathlib import Path

from pymatgen.io.vasp.outputs import Vasprun

from simmate.calculators.vasp.inputs.all import Incar, Poscar, Kpoints, Potcar
from simmate.workflow_engine.tasks.supervised_staged_shell_task import (
    SupervisedStagedShellTask as SSSTask,
)


def get_default_parallel_settings():
    # We load the user's default parallel settings from ~/.simmate/vasp/INCAR_parallel_settings
    # If this file doesn't exist, then we just use an empty dictionary
    settings_filename = os.path.join(
        Path.home(), ".simmate", "vasp", "INCAR_parallel_settings"
    )
    if os.path.exists(settings_filename):
        return Incar.from_file(settings_filename)
    else:
        return {}


class VaspTask(SSSTask):

    # Vasp calculations always need an input structure
    requires_structure = True

    # BUG:
    # Prefect is unfortunately unable access a task result's attribute when
    # building a flow. So I am unable to do things like...
    #
    #   with Workflow("example") as workflow:
    #       output = example_task()
    #       other_example_task(structure=output.structure)
    #
    # instead I need to make sure my output is a dictionary like so...
    #
    #   with Workflow("example") as workflow:
    #       output = example_task()
    #       other_example_task(structure=output["structure"])
    #
    # This controls whether we return just the result or a dict of result and
    # final structure. Really, the result (a Vasprun object) contains the final
    # structure via result.final_structure, BUT Prefect is causing problems here.
    # For now, I only set this to True during relaxations.
    return_final_structure = False

    # The command to call vasp in the current directory
    # TODO: add support for grabbing a user-set default from their configuration
    command = "vasp > vasp.out"

    # set the default vasp settings from a dictionary. This is the one thing
    # you *must* set when subclassing VaspTask. An example is:
    #   incar = dict(NSW=0, PREC="Accurate", KSPACING=0.5)
    incar = None

    # We also load any parallel settings to add on to the base incar. These
    # should not effect the calculation in any way, but they are still selected
    # based on the computer specs and what runs fastest on it. Therefore, these
    # settings are loaded from ~/.simmate/vasp/INCAR_parallel_settings by default.
    # This can also be overwritten as well.
    incar_parallel_settings = get_default_parallel_settings()

    # TODO: add options for poscar formation
    # add_selective_dynamics=False
    # add_velocities=False
    # significant_figures=6

    # set the KptGrid or KptPath object
    # TODO - KptGrid is just a float for now
    # NOTE - this is optional because you can have KSPACING as an INCAR argument.
    # If KSPACING is set above, we ignore whatever is set here.
    kpoints = None

    # This directs which Potcar files to grab. You would set this to a string
    # of what you want, such as "PBE", "PBE_GW", or "LDA"
    functional = None

    # This is an optional parameter to override Simmate's default selection of
    # potentials based off of the functional chosen. The defaults are located
    # in simmate.calculators.vasp.inputs.potcar_mappings. You can supply your
    # own mapping dictionary or you can take ours and update the specific
    # potentials you'd like. For example:
    #   from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
    #   element_mappings = PBE_ELEMENT_MAPPINGS.copy().update({"C": "C_h"})
    # or if you only use Carbon and don't care about other elements...
    #   element_mappings = {"C": "C_h"}
    # Read more on this inside the Potcar class and be careful with updating!
    potcar_mappings = None

    # In somecases we still want results from calculations that did NOT converge
    # successfully. This flag controls whether or not we raise an error when
    # the calculation failed to converge.
    # OPTIMIZE: What if I updated the ErrorHandler class to allow for "warnings"
    # instead of raising the error and applying the correction...? This functionality
    # could then be moved to the UnconvergedErrorHandler. I'd have a fix_error=True
    # attribute that is used in the .check() method. and If fix_error=False, I
    # simply print a warning & also add that warning to simmate_corrections.csv
    confirm_convergence = True

    # In some cases, we may want to sanitize the structure during our setup().
    # This means converting to the LLL-reduced primitive cell.
    pre_sanitize_structure = False

    def __init__(
        self,
        incar=None,
        kpoints=None,
        functional=None,
        potcar_mappings=None,
        confirm_convergence=None,
        pre_sanitize_structure=None,
        # To support other options from the Simmate SSSTask and Prefect Task
        **kwargs,
    ):

        # if any of these input parameters were given, overwrite the default
        # Note to python devs: this odd formatting is because we set our defaults
        # to None in __init__ while our actual default values are define above
        # as class attributes. This may seem funky at first glance, but it
        # makes inheriting from this class extremely pretty!
        # This code is effectively the same as @defaults_from_attrs(...)
        if incar:
            self.incar = incar
        if kpoints:
            self.kpoints = kpoints
        if functional:
            self.functional = functional
        if potcar_mappings:
            self.potcar_mappings = potcar_mappings
        if confirm_convergence:
            self.confirm_convergence = confirm_convergence
        if pre_sanitize_structure:
            self.pre_sanitize_structure = pre_sanitize_structure

        # now inherit from parent SSSTask class
        super().__init__(**kwargs)

    def setup(self, structure, directory):

        # If requested, we convert to the LLL-reduced unit cell, which aims to
        # be as cubic as possible.
        if self.pre_sanitize_structure:
            structure = structure.copy(sanitize=True)

        # write the poscar file
        Poscar.to_file(structure, os.path.join(directory, "POSCAR"))

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**self.incar) + Incar(**self.incar_parallel_settings)
        incar.to_file(
            filename=os.path.join(directory, "INCAR"),
            structure=structure,
        )

        # if KSPACING is not provide in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if self.kpoints and ("KSPACING" not in self.incar):
            Kpoints.to_file(
                structure,
                self.kpoints,
                os.path.join(directory, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure.composition.elements,
            self.functional,
            os.path.join(directory, "POTCAR"),
            self.potcar_mappings,
        )

    def workup(self, directory):
        """
        This is the most basic VASP workup where I simply load the final structure,
        final energy, and (if requested) confirm convergence. I will likely make
        this a common function for this vasp module down the road.
        """

        # load the xml file and all of the vasprun data
        try:
            vasprun = Vasprun(
                filename=os.path.join(directory, "vasprun.xml"),
                exception_on_bad_xml=True,
            )
        except:
            print(
                "XML is malformed. This typically means there's an error with your"
                " calculation that wasn't caught by your ErrorHandlers. We try"
                " salvaging data here though."
            )
            vasprun = Vasprun(
                filename=os.path.join(directory, "vasprun.xml"),
                exception_on_bad_xml=False,
            )
            vasprun.final_structure = vasprun.structures[-1]
        # BUG: This try/except is 100% just for my really rough calculations
        # where I don't use any ErrorHandlers and still want the final structure
        # regarless of what when wrong. In the future, I should consider writing
        # a separate method for those that loads the CONTCAR and moves on.

        # grab the final structure
        # final_structure = vasprun.structures[-1]

        # grab the energy per atom
        # final_energy = vasprun.final_energy / final_structure.num_sites

        # confirm that the calculation converged (ionicly and electronically)
        if self.confirm_convergence:
            assert vasprun.converged

        # OPTIMIZE: see my comment above on this attribute
        if self.return_final_structure:
            return {"structure_final": vasprun.final_structure, "vasprun": vasprun}

        # return vasprun object
        return vasprun

    @classmethod
    def get_config(cls):
        """
        Grabs the overall settings from the class. This is useful for printing out
        settings for users to inspect.
        """
        return {
            key: getattr(cls, key)
            for key in [
                "__module__",
                "incar",
                "pre_sanitize_structure",
                "incar",
                "functional",
                "potcar_mappings",
                "confirm_convergence",
            ]
        }
