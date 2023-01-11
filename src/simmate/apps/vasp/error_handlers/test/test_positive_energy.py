# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import PositiveEnergy
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_positive_energy(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="positive_energy",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    oszicar_filename = tmp_path / "OSZICAR"

    # init class with default settings
    error_handler = PositiveEnergy()

    # Confirm an error IS found using test files
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "halved POTIM from 0.5 to 0.25"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25

    # Confirm an error IS NOT found when the first ionic step hasn't completed yet
    # To check this, rewrite the OSZICAR file to only have the first line
    with oszicar_filename.open("r") as file:
        contents = file.readlines()
    with oszicar_filename.open("w") as file:
        file.writelines(contents[0])
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS NOT found when there is no OSZICAR
    oszicar_filename.unlink()
    assert error_handler.check(tmp_path) == False
