# -*- coding: utf-8 -*-

import os

import pytest

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import LargeSigma


def test_large_sigma(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="large_sigma",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    outcar_filename = os.path.join(tmpdir, "OUTCAR")

    # init class with default settings
    error_handler = LargeSigma()

    # Confirm an error IS found
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "reduced SIGMA from 0.1 to 0.04000000000000001"
    assert Incar.from_file(incar_filename)["SIGMA"] == 0.04000000000000001

    # Make 2nd attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched KSPACING from 0.5 to 0.4"
    assert Incar.from_file(incar_filename)["KSPACING"] == 0.4

    # Make final attempt at fixing the error, which raises an error
    incar = Incar.from_file(incar_filename)
    incar["KSPACING"] = 0.2
    incar.to_file(incar_filename)
    with pytest.raises(Exception):
        fix = error_handler.correct(tmpdir)

    # Confirm an error IS NOT found when no outcar exists
    os.remove(outcar_filename)
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS NOT found when ISMEAR > 0
    incar = Incar.from_file(incar_filename)
    incar["ISMEAR"] = -1
    incar.to_file(incar_filename)
    assert error_handler.check(tmpdir) == False
