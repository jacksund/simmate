# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import Potim


def test_potim(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="potim",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    oszicar_filename = os.path.join(tmpdir, "OSZICAR")

    # init class with default settings
    error_handler = Potim()

    # Confirm an error IS found using test files
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched IBRION to 3 and SMASS to 0.75"
    incar = Incar.from_file(incar_filename)
    assert incar["IBRION"] == 3
    assert incar["SMASS"] == 0.75

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched SYMPREC to 1e-8"
    assert Incar.from_file(incar_filename)["SYMPREC"] == 1e-8

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "halved the POTIM from 0.01 to 0.005"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.005

    # Confirm an error IS NOT found when there is no OSZICAR
    os.remove(oszicar_filename)
    assert error_handler.check(tmpdir) == False
