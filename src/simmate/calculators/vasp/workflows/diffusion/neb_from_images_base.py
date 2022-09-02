# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from simmate.calculators.vasp.inputs import Incar, Poscar, Potcar
from simmate.calculators.vasp.workflows.base import VaspWorkflow
from simmate.toolkit.diffusion import MigrationImages


class VaspNebFromImagesWorkflow(VaspWorkflow):
    """
    A base class for Nudged Elastic Band (NEB) calculations. This is not meant
    to be used directly but instead should be inherited from.

    Note, NEB tasks are very different from all other VASP tasks!

    The first big difference is that it takes a list of structures instead of
    just one structure. This means that instead of "structure=...", you should
    actually do "structures=[structure1, structure2, structure3, ...]", where
    the list of structures is your list of images.

    The second big difference is that VASP uses a different folder setup when
    running these calculations. It has a series of folders named 00, 01, 02, ... N,
    where 00 is the starting image, N is the endpoint image, and 01 to (N-1) are
    the midpoint images. Simmate handles this inside the task, but knowing this
    may be useful if you'd like to make your own variation of this class.
    """

    _parameter_methods = VaspWorkflow._parameter_methods.copy()
    _parameter_methods.remove("_get_clean_structure")

    # NEB does not require a POSCAR file because input structures are organized
    # into folders.
    required_files = ["INCAR", "POTCAR"]

    description_doc_short = "runs NEB using a series of structures images as input"

    @classmethod
    def setup(
        cls,
        directory: Path,
        migration_images: MigrationImages,
        **kwargs,
    ):
        """
        Writes input files for a NEB calculation. Each structure image recieves
        it's own folder within the parent directory.
        """

        # run some prechecks to make sure the user has everything set up properly.

        # One common mistake is to mislabel the number of images in the
        # INCAR file.
        # first, we check if the user set this.
        nimages = cls.incar.get("IMAGES")
        if nimages:
            # if so, we check that it was set correctly. It should be equal to
            # the number of structures minus 2 (because we don't count the
            # start and end images here.)
            if nimages != (len(migration_images) - 2):
                raise Exception(
                    "IMAGES looks to be improperly set! This value should not"
                    " include the start/end images -- so make sure you counted"
                    " properly. Alternatively, you also can remove this keyword"
                    " from your INCAR and Simmate will provide it automatically"
                    " for you."
                )

        # TODO: add a precheck that ensures the number of cores VASP is ran on
        # is also divisible by the number of images. For example...
        # "mpirun -n 16 vasp" will not work for IMAGES=3 because 16 is not
        # divisible by 3. But this also may be better suited for an ErrorHandler.
        # An example error message from from VASP is...
        #       "M_divide: can not subdivide 16 nodes by 3"

        # Here, each image (start to end structures) is put inside of its own
        # folder. We make those folders here, where they are named 00, 01, 02...N
        # Also recall that "structure" is really a list of structures here.
        for i, image in enumerate(migration_images):

            # first make establish the foldername
            # The zfill function converts numbers from "1" to "01" for us
            foldername = directory / str(i).zfill(2)
            # see if the folder exists, and if not, make it
            if not foldername.exists():
                foldername.mkdir()
            # now write the poscar file inside the folder
            Poscar.to_file(image, foldername / "POSCAR")

        # We also need to check if the user set IMAGES in the INCAR. If not,
        # we set that for them here. Note, we use the "pop" method which removes
        # the IMAGES__auto while grabbing its value. Because we are modifying
        # the incar dictionary here, we must make a copy of it -- this ensures
        # no bugs when this task is called in parallel.
        incar = cls.incar.copy()
        # !!! Should this code be moved to the INCAR class? Or would that require
        # too much reworking to allow INCAR to accept a list of structures?
        if not incar.get("IMAGES") and incar.pop("IMAGES__auto", None):
            incar["IMAGES"] = len(migration_images) - 2

        # Combine our base incar settings with those of our parallel settings
        # and then write the incar file
        incar = Incar(**incar) + Incar(**cls.incar_parallel_settings)
        incar.to_file(
            filename=directory / "INCAR",
            # we can use the start image for our structure -- as all structures
            # should give the same result.
            structure=migration_images[0],
        )

        # if KSPACING is not provided in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if cls.kpoints and ("KSPACING" not in cls.incar):
            raise Exception(
                "Custom KPOINTS are not supported by Simmate yet. "
                "Please use KSPACING in your INCAR instead."
            )

        # write the POTCAR file in this folder as well. Only one is needed and
        # all images will use refer to this POTCAR in the base directory
        Potcar.to_file_from_type(
            # we can use the start image for our structure -- as all structures
            # should give the same result.
            migration_images[0].composition.elements,
            cls.functional,
            directory / "POTCAR",
            cls.potcar_mappings,
        )

        # For the user's reference, we also like to write an image of the
        # starting path to a cif file. This can be slow for large structures
        # (>1s), but it is very little time compared to a full NEB run.
        path_vis = migration_images.get_sum_structure()
        path_vis.to("cif", directory / "simmate_path_relaxed_idpp.cif")

    @classmethod
    def setup_restart(cls, directory: Path, **kwargs):
        """
        From a working directory of a past calculation, sets up for the calculation
        to be restarted.
        """
        logging.warning("CONTCARs are not yet copied to POSCARs for NEB restarts.")

        # establish filenames
        stopcar_filename = directory / "STOPCAR"

        # delete the stopcar if it exists
        if stopcar_filename.exists():
            stopcar_filename.unlink()
