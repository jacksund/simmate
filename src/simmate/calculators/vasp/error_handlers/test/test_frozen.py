# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.error_handlers import Frozen
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files, make_dummy_files


def test_frozen(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="frozen",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    out_filename = tmp_path / "vasp.out"
    chgcar_filename = tmp_path / "CHGCAR"
    wavecar_filename = tmp_path / "WAVECAR"

    # We use a negative timeout to ensure this class fails
    error_handler = Frozen(timeout_limit=-1)

    # Confirm an error IS found
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error (with IMIX present)
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "Removed IMIX=1 and deleted CHGCAR and WAVECAR"
    assert not Incar.from_file(incar_filename).get("IMIX", None)
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO from Fast to Normal"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched SYMPREC from 1e-5 to 1e-8"
    assert Incar.from_file(incar_filename)["SYMPREC"] == 1e-08

    # Make final attempt at fixing the error, which raises an error
    with pytest.raises(Exception):
        fix = error_handler.correct(tmp_path)

    # Confirm an error IS NOT found when no file exists
    out_filename.unlink()
    assert error_handler.check(tmp_path) == False
