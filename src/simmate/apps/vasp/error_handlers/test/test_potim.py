# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import Potim
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_potim(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="potim",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    oszicar_filename = tmp_path / "OSZICAR"

    # init class with default settings
    error_handler = Potim()

    # Confirm an error IS found using test files
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched IBRION to 3 and SMASS to 0.75"
    incar = Incar.from_file(incar_filename)
    assert incar["IBRION"] == 3
    assert incar["SMASS"] == 0.75

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched SYMPREC to 1e-8"
    assert Incar.from_file(incar_filename)["SYMPREC"] == 1e-8

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "halved the POTIM from 0.01 to 0.005"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.005

    # Confirm an error IS NOT found when there is no OSZICAR
    oszicar_filename.unlink()
    assert error_handler.check(tmp_path) == False
