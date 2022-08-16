# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import Eddrmm
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files, make_dummy_files


def test_eddrmm(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="eddrmm",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    chgcar_filename = tmp_path / "CHGCAR"
    wavecar_filename = tmp_path / "WAVECAR"

    # init class with default settings
    error_handler = Eddrmm()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ALGO to Normal and deleted CHGCAR + WAVECAR"
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()

    # Make second attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "switch POTIM from 0.5 to 0.25 and deleted CHGCAR + WAVECAR"
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()


def test_eddrmm_neb(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="eddrmm_neb",
    )
    # This test is identical to test_eddrmm but with an NEB folder organization

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    # These files exist within a series of directories 00, 01,..., 05
    chgcar_filenames = [tmp_path / str(n).zfill(2) / "CHGCAR" for n in range(5)]
    wavecar_filenames = [tmp_path / str(n).zfill(2) / "WAVECAR" for n in range(5)]

    # init class with default settings
    error_handler = Eddrmm()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    make_dummy_files(*chgcar_filenames, *wavecar_filenames)
    fix = error_handler.correct(tmp_path)
    assert (
        fix == "switched ALGO to Normal and deleted CHGCARs + WAVECARs for all images"
    )
    assert Incar.from_file(incar_filename)["ALGO"] == "Normal"
    assert not any([f.exists() for f in chgcar_filenames])
    assert not any([f.exists() for f in wavecar_filenames])

    # Make second attempt at fixing the error
    make_dummy_files(*chgcar_filenames, *wavecar_filenames)
    fix = error_handler.correct(tmp_path)
    assert (
        fix
        == "switch POTIM from 0.5 to 0.25 and deleted CHGCARs + WAVECARs for all images"
    )
    assert Incar.from_file(incar_filename)["POTIM"] == 0.25
    assert not any([f.exists() for f in chgcar_filenames])
    assert not any([f.exists() for f in wavecar_filenames])
