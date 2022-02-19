# -*- coding: utf-8 -*-

import os
from pathlib import Path

import yaml

from pymatgen.io.vasp.outputs import Vasprun

from simmate.toolkit import Structure
from simmate.calculators.vasp.inputs import Incar, Poscar, Kpoints, Potcar
from simmate.workflow_engine import S3Task


def get_default_parallel_settings():
    """
    We load the user's default parallel settings from
        ~/simmate/vasp/INCAR_parallel_settings
    If this file doesn't exist, then we just use an empty dictionary.
    """
    settings_filename = os.path.join(
        Path.home(), "simmate", "vasp", "INCAR_parallel_settings"
    )
    if os.path.exists(settings_filename):
        return Incar.from_file(settings_filename)
    else:
        return {}


class VaspTask(S3Task):

    requires_structure: bool = True
    """
    Vasp calculations always need an input structure, so this is always True.
    """

    command: str = "vasp_std > vasp.out"
    """
    The command to call vasp, which is typically vasp_std. To ensure error
    handlers work properly, make sure your command has "> vasp.out" at the end.
    """
    # TODO: add support for grabbing a user-set default from their configuration
    # TODO: add auto check for vasp.out ending

    incar: dict = None
    """
    This sets the default vasp settings from a dictionary. This is the one thing
    you *must* set when subclassing VaspTask. An example is:
        
    ``` python
      incar = dict(NSW=0, PREC="Accurate", KSPACING=0.5)
    ```
    """

    incar_parallel_settings: dict = get_default_parallel_settings()
    """
    The parallel settings to add on to the base incar. These should not effect 
    the calculation result in any way (only how fast it completes), but they 
    are still selected based on the computer specs and what runs fastest on it.
    Therefore, these settings are loaded from ~/simmate/vasp/INCAR_parallel_settings
    by default and adding to this file should be the preferred method for updating
    these settings.
    """

    # TODO: add options for poscar formation
    # add_selective_dynamics=False
    # add_velocities=False
    # significant_figures=6 --> rounding issues? what's the best way to do this?

    kpoints = None
    """
    (experimental feature)
    The KptGrid or KptPath generator used to create the KPOINTS file. Note,
    this attribute is optional becuase VASP supports setting Kpts by adding
    KSPACING to the INCAR. If KSPACING is set in the INCAR, we ignore whatever 
    is set here.
    """
    # TODO - KptGrid is just a float for now, so there's no typing here.

    functional: str = None
    """
    This directs which Potcar files to grab. You would set this to a string
    of what you want, such as "PBE", "PBE_GW", or "LDA".
    """

    potcar_mappings: dict = None
    """
    This is an optional parameter to override Simmate's default selection of
    potentials based off of the functional chosen. The defaults are located
    in simmate.calculators.vasp.inputs.potcar_mappings. You can supply your
    own mapping dictionary or update the specific potentials you'd like. 
    For example:
    
    ``` python
      from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
      element_mappings = PBE_ELEMENT_MAPPINGS.copy()  # don't forget to copy!
      element_mappings.update({"C": "C_h"})  # if you wish to update any
    ```
    
    or if you only use Carbon and don't care about other elements...
    
    ``` python
      element_mappings = {"C": "C_h"}
    ```
    
    Read more on this inside the Potcar class and be careful with updating!
    """

    confirm_convergence: bool = True
    """
    This flag controls whether or not we raise an error when the calculation 
    failed to converge. In somecases we still want results from calculations 
    that did NOT converge successfully.
    """
    # OPTIMIZE: What if I updated the ErrorHandler class to allow for "warnings"
    # instead of raising the error and applying the correction...? This functionality
    # could then be moved to the UnconvergedErrorHandler. I'd have a fix_error=True
    # attribute that is used in the .check() method. and If fix_error=False, I
    # simply print a warning & also add that warning to simmate_corrections.csv

    pre_sanitize_structure: bool = False
    """
    In some cases, we may want to sanitize the structure during our setup().
    This means converting to the LLL-reduced primitive cell. This simply does:
    ``` python
    structure_sanitzed = structure.copy(santize=True)
    ```
    """

    pre_standardize_structure: bool = False
    """
    (experimental feature)
    In some cases, we may want to convert the structure to the standard primitive
    of a structure. For example, this is required when calculating band structures
    and ensuring we have a standardized high-symmetry path.
    """
    # TODO: not implemented yet

    def setup(self, structure: Structure, directory: str):

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

        # if KSPACING is not provided in the incar AND kpoints is attached to this
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

    def workup(self, directory: str):
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

        # write output files/plots for the user to quickly reference
        self._write_output_summary(directory, vasprun)

        # confirm that the calculation converged (ionicly and electronically)
        if self.confirm_convergence:
            assert vasprun.converged

        # return vasprun object
        return vasprun

    def _write_output_summary(self, directory: str, vasprun: Vasprun):
        """
        This is an EXPERIMENTAL feature.

        This prints a "simmate_summary.yaml" file with key output information.

        This method should not be called directly as it used within workup().
        """
        # OPTIMIZE: Ideally, I could take the vasprun object and run to_json,
        # but this output is extremely difficult to read.

        results = vasprun.as_dict()["output"]

        summary = {
            "structure_final": "The final structure is located in the CONTCAR file",
            "energy_final": float(results.get("final_energy", None)),
            "energy_final_per_atom": float(results.get("final_energy_per_atom", None)),
            "converged_electroinc": vasprun.converged_electronic,
            "converged_ionic": vasprun.converged_ionic,
            "fermi_energy": results.get("efermi", None),
            "valence_band_maximum": results.get("vbm", None),
            "conduction_band_minimum": results.get("vbm", None),
        }

        summary_filename = os.path.join(directory, "simmate_summary.yaml")
        with open(summary_filename, "w") as file:
            content = yaml.dump(summary)
            file.write(content)

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
                "pre_sanitize_structure",
                "confirm_convergence",
                "functional",
                "incar",
                "potcar_mappings",
            ]
        }
