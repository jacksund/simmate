# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import TetrahedronMesh


def test_tetrahedron_mesh(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="tetrahedron_mesh",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")

    # init class with default settings
    error_handler = TetrahedronMesh()

    # Confirm an error IS found using test files
    assert error_handler.check(tmpdir) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmpdir)
    assert fix == "switched KSPACING from 0.6 to 0.48"
    assert Incar.from_file(incar_filename)["KSPACING"] == 0.48

    # Make second attempt at fixing the error, for when we have the default
    # KSPACING value.
    incar = Incar.from_file(incar_filename)
    incar["KSPACING"] = 0.5
    incar.to_file(incar_filename)
    fix = error_handler.correct(tmpdir)
    assert fix == "switched ISMEAR to 0 and SIGMA to 0.05"
    incar = Incar.from_file(incar_filename)
    assert incar["ISMEAR"] == 0
    assert incar["SIGMA"] == 0.05

    # Confirm an error IS NOT found when there is no vasp.out
    error_handler.filename_to_check = "vasp.does_not_exist"
    assert error_handler.check(tmpdir) == False
