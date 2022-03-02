# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import IncorrectSmearing


def test_incorrect_smearing(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="incorrect_smearing",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")

    # init class with default settings
    error_handler = IncorrectSmearing()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasprun.does_not_exist"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasprun.xml"
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ISMEAR to 2 amd SIGMA to 0.2"
    assert Incar.from_file(incar_filename)["ISMEAR"] == 2
    assert Incar.from_file(incar_filename)["SIGMA"] == 0.2
