# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import Unconverged


def test_unconverged_electronic(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="unconverged_electronic",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    vasprun_filename = os.path.join(tmpdir, "vasprun.xml")

    # Confirm an error IS found when we have an unconverging xml
    error_handler = Unconverged()
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO from VeryFast to Fast"
    assert Incar.from_file(incar_filename)["ALGO"] == "Fast"

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO from Normal to All"
    assert Incar.from_file(incar_filename)["ALGO"] == "All"

    # Make fourth attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == (
        "turned on mixing with the following settings: {'ISTART': 1, 'ALGO': "
        "'Normal', 'NELMDL': -6, 'BMIX': 0.001, 'AMIX_MAG': 0.8, 'BMIX_MAG': 0.001}"
    )
    incar = Incar.from_file(incar_filename)
    assert incar["ISTART"] == 1
    assert incar["ALGO"] == "Normal"
    assert incar["NELMDL"] == -6
    assert incar["BMIX"] == 0.001
    assert incar["AMIX_MAG"] == 0.8
    assert incar["BMIX_MAG"] == 0.001

    # make sure no error is raised when the xml doesn't exist
    os.remove(vasprun_filename)
    assert error_handler.check(tmpdir) == False


def test_unconverged_ionic(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="unconverged_ionic",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    # Confirm an error IS found when we have an unconverging xml
    error_handler = Unconverged()
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "copied the CONTCAR into the POSCAR and switched IBRION to 1"
    assert Incar.from_file(incar_filename)["IBRION"] == 1
