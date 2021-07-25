# -*- coding: utf-8 -*-

import os

from simmate.calculators.vasp.inputs.all import Incar, Poscar, Kpoints, Potcar
from simmate.calculators.vasp.tasks.base import VaspTask

# NOTE TO USER:
# This NEB task is very different from all other VASP tasks!
#
# The first big difference is that it takes a list of structures instead of
# just one structure. This means when you set "structure=..." that you should
# actually do "structure=[structure1, structure2, structure3, ...]". This would
# be clearer if we made this input variable named "structures" instead of just
# "structure", but this requires more reworking on Simmate's end, and we
# unfortunately haven't had time to fix it yet.
#
# The second big difference is that VASP uses a different folder setup when
# running these calculations. It has a series of folders named 00, 01, 02, ... N,
# where 00 is the starting image, N is the endpoint image, and 01 to (N-1) are
# the pathway images. Simmate handles this inside the task, but knowing this
# may be useful if you'd like to make your own variation of this class.


class NudgedElasticBandTask(VaspTask):

    # The default settings to use for this calculation.
    # To tell VASP that we are doing an NEB calculation, we need to set the
    # IMAGES
    incar = dict(
        EDIFF=1.0e-07,
        ENCUT=520,
        ISMEAR=0,
        LCHARG=False,
        LWAVE=False,
        NSW=0,
        PREC="Accurate",
        SIGMA=0.05,
        # TODO: Allow IMAGES to be set like shown below.
        # For this, we use "__auto" to let Simmate set this automatically by
        # using the input structures given.
        # IMAGES__auto=True,
    )

    # We will use the PBE functional with all default mappings
    functional = "PBE"

    def _pre_checks(self, structure, dir):
        # This function is used inside of this class's setup method (shown below),
        # where we make sure the user has everything set up properly.

        # The first common mistake is that the user didn't provide a list of
        # structures as the input.
        if type(structure) != list:
            raise TypeError(
                "This task requires multiple structures given as a list! "
                "So your input should look like this..\n"
                "structure=[structure_start, structure_image1, structure_image2, ..., structure_end]"
                "\nWe apologize that this input can be confusing, and we'll "
                " work to fix this in the future!"
            )

        # The next common mistake is to mislabel the number of images in the INCAR
        # file.
        # first, we check if the user set this.
        nimages = self.incar.get("IMAGES")
        if nimages:
            # if so, we check that it was set correctly. It should be equal to
            # the number of structures minus 2 (because we don't count the
            # start and end images here.)
            if nimages != (len(structure) - 2):
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
        # divisible by 3.

    def setup(self, structure, dir):

        # run some prechecks to make sure the user has everything set up properly.
        self._pre_checks(structure, dir)

        # Here, each image (start to end structures) is put inside of its own
        # folder. We make those folders here, where they are named 00, 01, 02...N
        # Also recall that "structure" is really a list of structures here.
        for i, image in enumerate(structure):
            # first make establish the foldername
            # The zfill function converts numbers from "1" to "01" for us
            foldername = os.path.join(dir, str(i).zfill(2))
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
        Incar(**self.incar).to_file(os.path.join(dir, "INCAR"))

        # if KSPACING is not provided AND kpoints is, write the KPOINTS file
        if self.kpoints and ("KSPACING" not in self.incar):
            Kpoints.to_file(
                # We use the first image as all should give the same result
                structure[0],
                self.kpoints,
                os.path.join(dir, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            # We use the first image as all should give the same result
            structure[0].species,
            self.functional,
            os.path.join(dir, "POTCAR"),
            self.potcar_mappings,
        )
