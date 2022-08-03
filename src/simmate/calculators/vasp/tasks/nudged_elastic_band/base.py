# -*- coding: utf-8 -*-

import os
import shutil
import yaml
import numpy

from pymatgen.analysis.transition_state import NEBAnalysis

from simmate.toolkit.diffusion import MigrationImages
from simmate.calculators.vasp.inputs import Incar, Poscar, Potcar
from simmate.calculators.vasp.tasks.base import VaspTask


class VaspNudgedElasticBandTask(VaspTask):
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

    # NEB does not require a POSCAR file because input structures are organized
    # into folders.
    required_files = ["INCAR", "POTCAR"]

    # Pymatgen's NEB parser does not read from the vasprun.xml so it can't
    # confirm convergence here. I'll have to write my own output class to do this.
    confirm_convergence = False

    @classmethod
    def _pre_checks(
        cls,
        migration_images: MigrationImages,
        directory: str,
    ):
        """
        Runs a series of checks to ensure the user configured the job correctly.

        This is called automatically within the setup() method and shouldn't be
        used directly.
        """

        # The next common mistake is to mislabel the number of images in the
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

        # make sure all images are contained with the cell
        migration_images_cleaned = cls._process_structures(migration_images)
        return migration_images_cleaned

    @staticmethod
    def _process_structures(structures: MigrationImages):
        """
        Remove any atom jumps across the cell.

        This method is copied directly from pymatgen's MITNEBset and has not
        been refactored/reviewed yet.

        TODO: This code would be better placed as a method of MigrationImages
        """
        input_structures = structures
        structures = [input_structures[0]]
        for s in input_structures[1:]:
            prev = structures[-1]
            for i, site in enumerate(s):
                t = numpy.round(prev[i].frac_coords - site.frac_coords)
                if numpy.any(numpy.abs(t) > 0.5):
                    s.translate_sites([i], t, to_unit_cell=False)
            structures.append(s)
        return MigrationImages(structures)  # convert back to simmate object

    @classmethod
    def setup(
        cls,
        directory: str,
        migration_images: MigrationImages,
        **kwargs,
    ):
        """
        Writes input files for a NEB calculation. Each structure image recieves
        it's own folder within the parent directory.

        This method is typically not called directly. Instead, users should
        use the `run` method which calls setup within it.

        #### Parameters

        - `structure`:
            This parameter does NOTHING! NEB is a special-case workflow that
            accepts a list of structures instead of a single one. Therefore, it
            is strictly for compatibility with the core S3Task. Leave this
            value at None.

        - `directory`:
            The name of the directory to write all input files in. This directory
            should exists before calling. (see utilities.get_directory)

        - `structures`:
            The list of structures to use as a MigrationImages object.
        """
        # !!! The structure input is confusing for users, so I should consider
        # removing it from the S3Task...

        # run some prechecks to make sure the user has everything set up properly.
        migration_images_cleaned = cls._pre_checks(migration_images, directory)

        # Here, each image (start to end structures) is put inside of its own
        # folder. We make those folders here, where they are named 00, 01, 02...N
        # Also recall that "structure" is really a list of structures here.
        for i, image in enumerate(migration_images_cleaned):

            # first make establish the foldername
            # The zfill function converts numbers from "1" to "01" for us
            foldername = os.path.join(directory, str(i).zfill(2))
            # see if the folder exists, and if not, make it
            if not os.path.exists(foldername):
                os.mkdir(foldername)
            # now write the poscar file inside the folder
            Poscar.to_file(image, os.path.join(foldername, "POSCAR"))

        # We also need to check if the user set IMAGES in the INCAR. If not,
        # we set that for them here. Note, we use the "pop" method which removes
        # the IMAGES__auto while grabbing its value. Because we are modifying
        # the incar dictionary here, we must make a copy of it -- this ensures
        # no bugs when this task is called in parallel.
        incar = cls.incar.copy()
        # !!! Should this code be moved to the INCAR class? Or would that require
        # too much reworking to allow INCAR to accept a list of structures?
        if not incar.get("IMAGES") and incar.pop("IMAGES__auto", None):
            incar["IMAGES"] = len(migration_images_cleaned) - 2

        # Combine our base incar settings with those of our parallel settings
        # and then write the incar file
        incar = Incar(**incar) + Incar(**cls.incar_parallel_settings)
        incar.to_file(
            filename=os.path.join(directory, "INCAR"),
            # we can use the start image for our structure -- as all structures
            # should give the same result.
            structure=migration_images_cleaned[0],
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
            migration_images_cleaned[0].composition.elements,
            cls.functional,
            os.path.join(directory, "POTCAR"),
            cls.potcar_mappings,
        )

        # For the user's reference, we also like to write an image of the
        # starting path to a cif file. This can be slow for large structures
        # (>1s), but it is very little time compared to a full NEB run.
        path_vis = migration_images_cleaned.get_sum_structure()
        path_vis.to("cif", os.path.join(directory, "path_relaxed_idpp.cif"))

    @classmethod
    def setup_restart(cls, directory: str, **kwargs):
        """
        From a working directory of a past calculation, sets up for the calculation
        to be restarted.
        """
        print("WARNING: CONTCARs are not yet copied to POSCARs for NEB restarts.")

        # establish filenames
        stopcar_filename = os.path.join(directory, "STOPCAR")

        # delete the stopcar if it exists
        if os.path.exists(stopcar_filename):
            os.remove(stopcar_filename)

    @classmethod
    def workup(cls, directory: str):
        """
        Works up data from a NEB run, including confirming convergence and
        writing summary output files (structures, data, and plots).

        #### Parameters

        - `directory`:
            Name of the base folder where all results are located.
        """
        # BUG: For now I assume there are start/end image directories are located
        # in the working directory. These relaxation are actually ran by a
        # separate workflow, which is thus a prerequisite for this workflow.
        start_dirname = os.path.join(directory, "relaxation.vasp.neb-endpoint.start")
        end_dirname = os.path.join(directory, "relaxation.vasp.neb-endpoint.end")
        try:
            assert os.path.exists(start_dirname)
            assert os.path.exists(end_dirname)
        except:
            raise Exception(
                "Your NEB calculation completed successfully. However, in order "
                "to run the workup, Simmate needs the start/end point relaxations. "
                "These should be in the same folder as your NEB run and named "
                "relaxation.vasp.neb-endpoint.start and relaxation.vasp.neb-endpoint.end."
            )

        ################
        # BUG: NEBAnalysis.from_dir is broken for all folder structures except
        # when the start/end points are in the 00 and N folders. I therefore
        # need to copy the OUTCAR from the endpoint relaxations to these folders.
        # I don't want to mess with opening a pull request with them / waiting
        # on a new release, so I make this hacky fix here
        new_start_filename = os.path.join(directory, "00", "OUTCAR")

        # the end filename should be the highest number in the directory
        numbered_dirs = [d for d in os.listdir(directory) if d.isdigit()]
        numbered_dirs.sort()
        new_end_filename = os.path.join(directory, numbered_dirs[-1], "OUTCAR")

        # now copy the outcars over
        shutil.copyfile(os.path.join(start_dirname, "OUTCAR"), new_start_filename)
        shutil.copyfile(os.path.join(end_dirname, "OUTCAR"), new_end_filename)
        ################

        neb_results = NEBAnalysis.from_dir(
            directory,
            # BUG: see bug fix right above this
            # relaxation_dirs=[
            #     "endpoint_relaxation_start",
            #     "endpoint_relaxation_end",
            # ],
        )

        # write output files/plots for the user to quickly reference
        cls._write_output_summary(directory, neb_results)

        return neb_results

    @staticmethod
    def _write_output_summary(directory: str, neb_results: NEBAnalysis):
        """
        This is an EXPERIMENTAL feature.

        This prints a "simmate_summary.yaml" file with key output information.

        This method should not be called directly as it used within workup().
        """

        # plot the results
        # plot = neb_results.get_plot()
        # plot.savefig(os.path.join(directory, "NEB_plot.jpeg"))
        print(
            "NEB plot generation is temporarily disabled due to a bug in prefect "
            "where matplotlib.plot() leads to a segmentation fault. "
            "See https://github.com/PrefectHQ/prefect/issues/5991"
        )

        # convert all the structures to a MigrationImages object so we can write
        # the summed structure.
        migration_images = MigrationImages(neb_results.structures)
        structure_sum = migration_images.get_sum_structure()
        structure_sum.to("cif", os.path.join(directory, "path_relaxed_neb.cif"))

        results_dict = neb_results.as_dict()
        summary = {
            "structures": "Final structure images are the CONTCARs within image directories (00-N)",
            "forces_tangent": results_dict["forces"],
            "energies": results_dict["energies"],
            "structure_distances": results_dict["r"],
            "energy_barrier": float(
                max(neb_results.energies) - min(neb_results.energies)
            ),
        }

        summary_filename = os.path.join(directory, "simmate_summary.yaml")
        with open(summary_filename, "w") as file:
            content = yaml.dump(summary)
            file.write(content)
