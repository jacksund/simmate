# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.calculators.vasp.inputs import Incar, Kpoints, Poscar, Potcar
from simmate.toolkit import Structure
from simmate.workflow_engine import S3Workflow


def get_default_parallel_settings():
    """
    We load the user's default parallel settings from
        ~/simmate/vasp/INCAR_parallel_settings
    If this file doesn't exist, then we just use an empty dictionary.
    """
    settings_filename = Path.home() / "simmate" / "vasp" / "INCAR_parallel_settings"
    if settings_filename.exists():
        return Incar.from_file(settings_filename)
    else:
        return {}


class VaspWorkflow(S3Workflow):

    _parameter_methods = S3Workflow._parameter_methods + ["_get_clean_structure"]

    required_files = ["INCAR", "POTCAR", "POSCAR"]

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
    you *must* set when subclassing VaspWorkflow. An example is:
        
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

    standardize_structure: str | bool = False
    """
    In some cases, we may want to standardize the structure during our setup().
    
    This means running symmetry analysis on the structure in order to reduce
    the symmetry and also converting it to some standardized form. There
    are three different forms to choose from and thus 3 different values that
    `standardize_structure` can be set to:
    
    - `primitive`: for the standard primitive unitcell
    - `conventional`: for the standard conventional unitcell
    - `primitive-LLL`: for the standard primitive unitcell that is then LLL-reduced
    - `False`: this is the default and will disable this feature
    
    We recommend using `primitive-LLL` when the smallest possible and most cubic
    unitcell is desired.
    
    We recommend using `primitive` when calculating band structures and 
    ensuring we have a standardized high-symmetry path. Note, existing band
    structure workflows automatically adjust this value for you.
    
    To control the tolerances used to symmetrize the structure, you can use the
    symmetry_precision and angle_tolerance attributes.
    
    By default, no standardization is applied.
    """

    symmetry_precision: float = 0.01
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the sites are symmetrically equivalent. (in Angstroms)
    """

    angle_tolerance: float = 0.5
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the angles between sites are symmetrically equivalent. (in Degrees)
    """

    @classmethod
    def _get_clean_structure(
        cls,
        structure: Structure,
        standardize_structure: str | bool = None,
        symmetry_precision: float = None,
        angle_tolerance: float = None,
        **kwargs,
    ) -> Structure:
        """
        Uses the class attribute for `standardize_structure`. If this is set
        to any of the listed modes, then the structure unitcell is converted
        using the proper methods.

        Note, this method is typically called within `setup` before any input
        files are written. You should never have to call it directly.
        """

        # See if these values were provided, or default to class attribute.
        # We rename this to "standardize mode" to accurately descibe the
        # variable if it is set
        standardize_mode = standardize_structure or cls.standardize_structure
        symmetry_precision = symmetry_precision or cls.symmetry_precision
        angle_tolerance = angle_tolerance or cls.angle_tolerance

        # if standardize_structure is not requested, then we just return the
        # orignal input structure.
        if not standardize_mode:

            return structure

        # Make sure the user
        if standardize_mode not in ["primitive-LLL", "conventional", "primitive"]:
            raise Exception(
                f"Standardization mode {standardize_mode} is not supported."
            )

        # Both cleaning steps start with looking at the symmetry analysis
        sym_finder = SpacegroupAnalyzer(
            structure,
            symprec=symmetry_precision,
            angle_tolerance=angle_tolerance,
        )

        # If requested, we convert to the LLL-reduced unit cell, which aims to
        # be as cubic as possible.
        if standardize_mode == "primitive-LLL":
            structure_prim = sym_finder.get_primitive_standard_structure()
            structure_cleaned = structure_prim.copy(sanitize=True)
            return structure_cleaned

        # For band structures, we need to make sure the structure is in the
        # standardized primitive form.
        if standardize_mode == "primitive":
            structure_cleaned = sym_finder.get_primitive_standard_structure(
                international_monoclinic=False,
            )
            # check for pymatgen bugs here
            check_for_standardization_bugs(structure, structure_cleaned)
            return structure_cleaned

        # lastly is the conventional standard, which is used the least.
        if standardize_mode == "conventional":
            structure_cleaned = sym_finder.get_conventional_standard_structure()
            return structure_cleaned

    @classmethod
    def setup(cls, directory: Path, structure: Structure, **kwargs):

        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        # write the poscar file
        Poscar.to_file(structure_cleaned, directory / "POSCAR")

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**cls.incar) + Incar(**cls.incar_parallel_settings)
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


def check_for_standardization_bugs(
    structure_original: Structure,
    structure_new: Structure,
):

    # In pymatgen, they include this code with the standardization of their
    # structures because there were several bugs in the past and they want to
    # double-check themselves. I'm still using their code to standardize
    # my structures, so I should make this check too.

    vpa_old = structure_original.volume / structure_original.num_sites
    vpa_new = structure_new.volume / structure_new.num_sites

    if abs(vpa_old - vpa_new) / vpa_old > 0.02:
        raise ValueError(
            "Standardizing failed! Volume-per-atom changed... "
            f"old: {vpa_old}, new: {vpa_new}"
        )

    sm = StructureMatcher()
    if not sm.fit(structure_original, structure_new):
        raise ValueError("Standardizing failed! Old structure doesn't match new.")
