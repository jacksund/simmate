# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import PositiveEnergy


def test_positive_energy(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="positive_energy",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    oszicar_filename = os.path.join(tmpdir, "OSZICAR")

    # init class with default settings
    error_handler = PositiveEnergy()

    # Confirm an error IS found using test files
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "halved POTIM from 0.5 to 0.25"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25

    # Confirm an error IS NOT found when the first ionic step hasn't completed yet
    # To check this, rewrite the OSZICAR file to only have the first line
    with open(oszicar_filename, "r") as file:
        contents = file.readlines()
    with open(oszicar_filename, "w") as file:
        file.writelines(contents[0])
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS NOT found when there is no OSZICAR
    os.remove(oszicar_filename)
    assert error_handler.check(tmpdir) == False
