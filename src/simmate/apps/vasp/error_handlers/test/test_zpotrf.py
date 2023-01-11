# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import Zpotrf
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files, make_dummy_files


def test_eddrmm(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="zpotrf",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    chgcar_filename = tmp_path / "CHGCAR"
    wavecar_filename = tmp_path / "WAVECAR"
    oszicar_filename = tmp_path / "OSZICAR"

    # init class with default settings
    error_handler = Zpotrf()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmp_path) == True

    # Attempt to fix the error when we have >1 valid ionic steps in the OSZICAR
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert (
        fix
        == "set ISYM to 0 and switched POTIM from 0.5 to 0.25 and deleted CHGCAR and WAVECAR"
    )
    incar = Incar.from_file(incar_filename)
    assert incar["ISYM"] == 0
    assert incar["POTIM"] == 0.25
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()

    # remove OSZICAR to the remaining checks/fixes
    oszicar_filename.unlink()

    # Make first attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "set ISYM to 0 and deleted CHGCAR and WAVECAR"
    incar = Incar.from_file(incar_filename)
    assert Incar.from_file(incar_filename)["ISYM"] == 0
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()

    # Make second attempt at fixing the error
    with incar_filename.open("w") as file:
        file.write("NSW = 1 \nISIF = 2")
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "scaled the structure lattice by +20% and deleted CHGCAR and WAVECAR"
