# -*- coding: utf-8 -*-

import os

import pytest

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import FrozenErrorHandler


def test_frozen(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="frozen",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    out_filename = os.path.join(tmpdir, "vasp.out")

    # We use a negative timeout to ensure this class fails
    error_handler = FrozenErrorHandler(timeout_limit=-1)

    # Confirm an error IS found
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched SYMPREC from 1e-5 to 1e-8"
    assert Incar.from_file(incar_filename)["SYMPREC"] == 1e-08

    # Make final attempt at fixing the error, which raises an error
    with pytest.raises(Exception):
        fix = error_handler.correct(tmpdir)

    # Confirm an error IS NOT found when no file exists
    os.remove(out_filename)
    assert error_handler.check(tmpdir) == False
