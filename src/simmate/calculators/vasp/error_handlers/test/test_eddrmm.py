# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import Eddrmm


def test_eddrmm(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="eddrmm",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    chgcar_filename = os.path.join(tmpdir, "CHGCAR")
    wavecar_filename = os.path.join(tmpdir, "WAVECAR")

    # init class with default settings
    error_handler = Eddrmm()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ALGO to Normal and deleted CHGCAR + WAVECAR"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"
    assert not os.path.exists(chgcar_filename)
    assert not os.path.exists(wavecar_filename)

    # Make second attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "switch POTIM from 0.5 to 0.25 and deleted CHGCAR + WAVECAR"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25
    assert not os.path.exists(chgcar_filename)
    assert not os.path.exists(wavecar_filename)


def test_eddrmm_neb(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="eddrmm_neb",
    )
    # This test is identical to test_eddrmm but with an NEB folder organization

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    # These files exist within a series of directories 00, 01,..., 05
    chgcar_filenames = [
        os.path.join(tmpdir, str(n).zfill(2), "CHGCAR") for n in range(5)
    ]
    wavecar_filenames = [
        os.path.join(tmpdir, str(n).zfill(2), "WAVECAR") for n in range(5)
    ]

    # init class with default settings
    error_handler = Eddrmm()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    make_dummy_files(*chgcar_filenames, *wavecar_filenames)
    fix = error_handler.correct(tmpdir)
    assert (
        fix == "switched ALGO to Normal and deleted CHGCARs + WAVECARs for all images"
    )
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"
    assert not any([os.path.exists(f) for f in chgcar_filenames])
    assert not any([os.path.exists(f) for f in wavecar_filenames])

    # Make second attempt at fixing the error
    make_dummy_files(*chgcar_filenames, *wavecar_filenames)
    fix = error_handler.correct(tmpdir)
    assert (
        fix
        == "switch POTIM from 0.5 to 0.25 and deleted CHGCARs + WAVECARs for all images"
    )
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25
    assert not any([os.path.exists(f) for f in chgcar_filenames])
    assert not any([os.path.exists(f) for f in wavecar_filenames])
