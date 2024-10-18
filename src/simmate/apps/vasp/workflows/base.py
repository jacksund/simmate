# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

from simmate.apps.vasp.inputs import Incar, Kpoints, Poscar, Potcar
from simmate.configuration import settings
from simmate.engine import S3Workflow, StructureWorkflow
from simmate.toolkit import Structure


def get_default_parallel_settings():
    """
    We load the user's default parallel settings for VASP, which optionally
    configure NCORE and KPAR for all workflows.

    These settings should not effect the calculation result in any way
    (only how fast it completes), but they are still selected based on
    the computer specs and what runs fastest on it.
    """
    parallel_settings = settings.vasp.parallelization

    if parallel_settings.ncore is not None or parallel_settings.kpar is not None:
        raise NotImplementedError(
            "NCORE and KPAR configuration settings are still under development"
        )
    else:
        return {}


class VaspWorkflow(S3Workflow, StructureWorkflow):
    _parameter_methods = S3Workflow._parameter_methods + StructureWorkflow._parameter_methods
    
    required_files = ["INCAR", "POTCAR", "POSCAR"]
    exclude_from_archives = ["POTCAR"]

    command: str = "vasp_std > vasp.out"
    """
    The command to call vasp, which is typically vasp_std. To ensure error
    handlers work properly, make sure your command has "> vasp.out" at the end.
    """
    # TODO: add support for grabbing a user-set default from their configuration
    # TODO: add auto check for vasp.out ending

    # -------------------------------------------------------------------------

    # INCAR configuration

    @classmethod
    @property
    def incar(cls) -> dict:
        """
        The INCAR configuration settings that will be used for this workflow.

        Note: do not confuse with `_incar` and `_incar_updates`, which are
        used to determine the final settings given by this `incar` property.
        """
        # OPTIMIZE: I'd like this to be cached
        if not cls._incar_updates:
            return cls._incar
        else:
            # grab the parent workflow to use as the base incar. The workflow
            # may have multiple parent classes (mix-ins), so we grab __bases__
            # instead of __base__
            parent_flows = cls.__bases__
            if len(parent_flows) == 1:
                parent_incar = cls.__base__.incar
            else:
                parent_incars_found = 0
                for parent_flow in parent_flows:
                    if parent_flow.incar:
                        parent_incar = parent_flow.incar
                        parent_incars_found = +1
                        # we do not break the loop in case there are errors, which
                        # we check for below
                if parent_incars_found > 1:
                    raise Exception(
                        "Your VaspWorkflow is inheriting from more than workflow "
                        "with valid `incar` settings. Therefore, it is not clear "
                        "which settings should be inherited in your subclass."
                    )
                elif parent_incars_found == 0:
                    raise Exception(
                        "Only use `_incar_updates` when the parent workflow has a "
                        "valid `incar` config set."
                    )
            # Note we always use copy() in the methods below because we
            # are modifying all values in-place
            updates = cls._incar_updates.copy()
            final_incar = parent_incar.copy()

            for key, value in updates.items():
                # Check if there is a modifier version of the key that
                # needs removed.
                # For example, a new "EDIFF" would replace "EDIFF__per_atom"
                for original_key in parent_incar.keys():
                    if original_key.split("__")[0] == key.split("__")[0]:
                        final_incar.pop(original_key)
                # OPIMIZE: maybe move this logic to the Incar class

                # now set the updated value
                if value == "__remove__":
                    final_incar.pop(value, None)
                else:
                    final_incar[key] = value

            return final_incar

    _incar: dict = {}
    """
    This sets the base vasp settings from a dictionary. This is the one thing
    you *must* set when subclassing VaspWorkflow. An example is:
    
    ``` python
      _incar = dict(NSW=0, PREC="Accurate", KSPACING=0.5)
    ```
    
    Note: you should refer to `incar` instead of this attribute for the final
    workflow settings of this class.
    """

    _incar_updates: dict = {}
    """
    When subclassing a subclass of `VaspWorkflow` (i.e. inheriting INCAR settings),
    this attribute helps to set which INCARs are changed relative to the parent
    workflow.
    """

    # -------------------------------------------------------------------------

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
    in `simmate.apps.vasp.inputs.potcar_mappings`. You can supply your
    own mapping dictionary or update the specific potentials you'd like. 
    For example:
    
    ``` python
      from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
      potcar_mappings = PBE_POTCAR_MAPPINGS.copy()  # don't forget to copy!
      potcar_mappings.update({"C": "C_h"})  # if you wish to update any
    ```
    
    or if you only use Carbon and don't care about other elements...
    
    ``` python
      potcar_mappings = {"C": "C_h"}
    ```
    
    Read more on this inside the Potcar class and be careful with updating!
    """

    @classmethod
    def setup(cls, directory: Path, structure: Structure, **kwargs):
        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        # write the poscar file
        Poscar.to_file(structure_cleaned, directory / "POSCAR")

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**cls.incar)
        incar.to_file(
            filename=directory / "INCAR",
            structure=structure_cleaned,
        )

        # if KSPACING is not provided in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if cls.kpoints and ("KSPACING" not in cls.incar):
            Kpoints.to_file(
                structure_cleaned,
                cls.kpoints,
                directory / "KPOINTS",
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure_cleaned.composition.elements,
            cls.functional,
            directory / "POTCAR",
            cls.potcar_mappings,
        )

    @classmethod
    def setup_restart(cls, directory: Path, **kwargs):
        """
        From a working directory of a past calculation, sets up for the calculation
        to be restarted. For relaxations/dynamics this involved just copying
        the poscar to the contcar.
        """

        # establish filenames
        poscar_filename = directory / "POSCAR"
        poscar_orig_filename = directory / "POSCAR_original"
        contcar_filename = directory / "CONTCAR"
        stopcar_filename = directory / "STOPCAR"

        # TODO:
        # make an archive of the directory before we start editting files
        # make_error_archive(directory)
        # add these changes to the simmate_corrections.csv

        # delete the stopcar if it exists
        if stopcar_filename.exists():
            stopcar_filename.unlink()

        # copy poscar to a new file
        shutil.move(poscar_filename, poscar_orig_filename)

        # then CONTCAR over to the POSCAR
        shutil.move(contcar_filename, poscar_filename)

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
                "functional",
                "incar",
                "potcar_mappings",
            ]
        }
