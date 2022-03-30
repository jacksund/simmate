# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import Zpotrf


def test_eddrmm(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="zpotrf",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    chgcar_filename = os.path.join(tmpdir, "CHGCAR")
    wavecar_filename = os.path.join(tmpdir, "WAVECAR")
    oszicar_filename = os.path.join(tmpdir, "OSZICAR")

    # init class with default settings
    error_handler = Zpotrf()

    # Confirm an error IS NOT found
    error_handler.filename_to_check = "vasp.no_error"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmpdir) == True

    # Attempt to fix the error when we have >1 valid ionic steps in the OSZICAR
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert (
        fix
        == "set ISYM to 0 and switched POTIM from 0.5 to 0.25 and deleted CHGCAR and WAVECAR"
    )
    incar = Incar.from_file(incar_filename)
    assert incar["ISYM"] == 0
    assert incar["POTIM"] == 0.25
    assert not os.path.exists(chgcar_filename)
    assert not os.path.exists(wavecar_filename)

    # remove OSZICAR to the remaining checks/fixes
    os.remove(oszicar_filename)

    # Make first attempt at fixing the error
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "set ISYM to 0 and deleted CHGCAR and WAVECAR"
    incar = Incar.from_file(incar_filename)
    assert Incar.from_file(incar_filename)["ISYM"] == 0
    assert not os.path.exists(chgcar_filename)
    assert not os.path.exists(wavecar_filename)

    # Make second attempt at fixing the error
    with open(incar_filename, "w") as file:
        file.write("NSW = 1 \nISIF = 2")
    make_dummy_files(chgcar_filename, wavecar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "scaled the structure lattice by +20% and deleted CHGCAR and WAVECAR"
