# -*- coding: utf-8 -*-

import os
import numpy

from pymatgen.analysis.transition_state import NEBAnalysis
from simmate.toolkit.diffusion import MigrationImages

from simmate.calculators.vasp.inputs import Incar, Poscar, Kpoints, Potcar
from simmate.calculators.vasp.tasks.relaxation.neb_endpoint import NEBEndpointRelaxation


class MITNudgedElasticBand(NEBEndpointRelaxation):
    """
    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.

    You typically shouldn't use this workflow directly, but instead use the
    higher-level NEB workflows (e.g. diffusion/neb_all_paths or
    diffusion/neb_from_endpoints), which call this workflow for you.


    Devs Notes
    ----------

    This NEB task is very different from all other VASP tasks!

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

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # These settings are based off of pymatgen's MVLCINEBSet, which inherts from
    # the MITNEBSet.
    # http://guide.materialsvirtuallab.org/pymatgen-analysis-diffusion/pymatgen.analysis.diffusion.neb.io.html
    # https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITNEBSet
    incar = NEBEndpointRelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=1,
            # TODO: Allow IMAGES to be set like shown below.
            # For this, we use "__auto" to let Simmate set this automatically by
            # using the input structures given.
            # len(structures) - 2,
            IMAGES__auto=True,
        )
    )

    requires_structure = False
    """
    This is a unique case for VASP calculations because the input is NOT a 
    single structure, but instead a list of structures -- spefically a list
    supercell images along the diffusion pathway.
    """

    def _pre_checks(
        self,
        structures: MigrationImages,
        directory: str,
        structure: None,
    ):
        """
        Runs a series of checks to ensure the user configured the job correctly.

        This is called automatically within the setup() method and shouldn't be
        used directly.
        """

        # The first common mistake is providing a structure instead of structures
        if structure:
            raise Exception(
                "This NEB calculation requires a list of structures (aka images). "
                "Make sure you provide the structures input and NOT a single "
                "structure."
            )

        # The next common mistake is to mislabel the number of images in the
        # INCAR file.
        # first, we check if the user set this.
        nimages = self.incar.get("IMAGES")
        if nimages:
            # if so, we check that it was set correctly. It should be equal to
            # the number of structures minus 2 (because we don't count the
            # start and end images here.)
            if nimages != (len(structures) - 2):
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
        self.structures = self._process_structures(structures)

    @staticmethod
    def _process_structures(
        structures: MigrationImages,
    ):
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
        return structures

    def setup(
        self,
        structure: None,
        directory: str,
        structures: MigrationImages,
    ):
        """
        Writes input files for a NEB calculation. Each structure image recieves
        it's own folder within the parent directory.

        This method is typically not called directly. Instead, users should
        use the `run` method which calls setup within it.

        Parameters
        ----------
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
        self._pre_checks(structures, directory, structure)

        # Here, each image (start to end structures) is put inside of its own
        # folder. We make those folders here, where they are named 00, 01, 02...N
        # Also recall that "structure" is really a list of structures here.
        for i, image in enumerate(structure):
            # first make establish the foldername
            # The zfill function converts numbers from "1" to "01" for us
            foldername = os.path.join(directory, str(i).zfill(2))
            # see if the folder exists, and if not, make it
            if not os.path.exists(foldername):
                os.mkdir(foldername)
            # now write the poscar file inside the folder
            Poscar.to_file(image, os.path.join(foldername, "POSCAR"))

        # We also need to check if the user set IMAGES in the INCAR. If not,
        # we set that for them here.
        if not self.incar.get("IMAGES"):
            self.incar["IMAGES"] = len(structure) - 2
        # BUG: changing this class attribute may not be safe to do when this
        # task is used accross multiple pathways with different image numbers.
        # It may be better to make a separate incar dictionary that we then pass
        # to Incar() below.

        # write the incar file
        Incar(**self.incar).to_file(os.path.join(directory, "INCAR"))

        # if KSPACING is not provided AND kpoints is, write the KPOINTS file
        if self.kpoints and ("KSPACING" not in self.incar):
            Kpoints.to_file(
                # We use the first image as all should give the same result
                structure[0],
                self.kpoints,
                os.path.join(directory, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            # We use the first image as all should give the same result
            structure[0].composition.elements,
            self.functional,
            os.path.join(directory, "POTCAR"),
            self.potcar_mappings,
        )

    def workup(
        self,
        directory: str,
    ):

        # BUG: For now I assume there are start/end image directories are located
        # in the working directory. This bad assumption is made as I'm just quickly
        # trying to get results for some labmates. In the future, I need to search
        # a number of places for these directories.
        neb_results = NEBAnalysis.from_dir(
            directory,
            relaxation_dirs=["start_image_relaxation", "end_image_relaxation"],
        )

        # plot the results
        plot = neb_results.get_plot()
        plot.savefig("NEB_plot.jpeg")
