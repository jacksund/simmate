# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.error_handlers import NonConverging
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_nonconverging(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="nonconverging",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    oszicar_filename = tmp_path / "OSZICAR"

    # Confirm an error IS NOT found when there aren't enough ionic steps
    error_handler = NonConverging()  # default is 10
    assert error_handler.check(tmp_path) == False

    # We limit this to 2 steps to ensure we get the error
    error_handler = NonConverging(min_ionic_steps=2)
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO from VeryFast to Fast"
    assert Incar.from_file(incar_filename)["ALGO"] == "Fast"

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO from Normal to All"
    assert Incar.from_file(incar_filename)["ALGO"] == "All"

    # Make fourth attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched linear mixing via {'AMIX': 0.1, 'BMIX': 0.01, 'ICHARG': 2}"
    incar = Incar.from_file(incar_filename)
    assert incar["AMIX"] == 0.1
    assert incar["BMIX"] == 0.01
    assert incar["ICHARG"] == 2

    # Make fifth attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched linear mixing via {'AMIN': 0.01, 'BMIX': 3.0, 'ICHARG': 2}"
    incar = Incar.from_file(incar_filename)
    assert incar["AMIN"] == 0.01
    assert incar["BMIX"] == 3.0
    assert incar["ICHARG"] == 2

    # Make final attempt at fixing the error, which raises an error
    with pytest.raises(Exception):
        fix = error_handler.correct(tmp_path)

    # Make sure an error is not raised when an electronic step converges
    incar = Incar.from_file(incar_filename)
    incar["NELM"] = 2
    incar.to_file(incar_filename)
    assert error_handler.check(tmp_path) == False

    # Make sure an error is not raised when no OSZICAR is present
    oszicar_filename.unlink()
    assert error_handler.check(tmp_path) == False
