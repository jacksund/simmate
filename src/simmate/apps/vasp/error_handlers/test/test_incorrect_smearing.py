# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import IncorrectSmearing
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_incorrect_smearing(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="incorrect_smearing.zip",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"

    # init class with default settings
    error_handler = IncorrectSmearing()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasprun.does_not_exist"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasprun.xml"
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ISMEAR to 2 amd SIGMA to 0.2"
    assert Incar.from_file(incar_filename)["ISMEAR"] == 2
    assert Incar.from_file(incar_filename)["SIGMA"] == 0.2
