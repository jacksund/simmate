# -*- coding: utf-8 -*-

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import Brmix


def test_brmix(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="brmix.zip",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmpdir / "INCAR"
    chgcar_filename = tmpdir / "CHGCAR"
    wavecar_filename = tmpdir / "WAVECAR"
    outcar_filename = tmpdir / "OUTCAR"
    errorcount_filename = tmpdir / "simmate_error_counts.json"

    # init class with default settings
    error_handler = Brmix()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmpdir) == True

    # Handle error when there is a valid OUTCAR
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ISTART to 1"
    incar = Incar.from_file(incar_filename)
    assert incar["ISTART"] == 1

    # Remove the error counts and valid OUTCAR and restart
    errorcount_filename.unlink()
    outcar_filename.unlink()

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched IMIX to 1"
    incar = Incar.from_file(incar_filename)
    assert incar["IMIX"] == 1

    # Make second attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "removed any IMIX tag and switched KGAMMA to False"
    incar = Incar.from_file(incar_filename)
    assert incar.get("IMIX", None) == None
    assert incar["KGAMMA"] == False

    # Make third attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "removed any IMIX tag and switched KGAMMA to True"
    incar = Incar.from_file(incar_filename)
    assert incar.get("IMIX", None) == None
    assert incar["KGAMMA"] == True

    # Make final attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ISYM to 0 and KGAMMA to True and deleted CHGCAR and WAVECAR"
    incar = Incar.from_file(incar_filename)
    assert incar["ISYM"] == 0
    assert incar["KGAMMA"] == True
    assert not chgcar_filename.exists()
    assert not wavecar_filename.exists()

    # Confirm an error IS NOT found when NELECT is in the INCAR
    with open(incar_filename, "w") as file:
        file.write("NELECT = 123")
    assert error_handler.check(tmpdir) == False
