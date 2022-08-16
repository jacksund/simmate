# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import TetrahedronMesh
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_tetrahedron_mesh(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="tetrahedron_mesh",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"

    # init class with default settings
    error_handler = TetrahedronMesh()

    # Confirm an error IS found using test files
    assert error_handler.check(tmp_path) == True

    # Make first attempt at fixing the error
    fix = error_handler.correct(tmp_path)
    assert fix == "switched KSPACING from 0.6 to 0.48"
    assert Incar.from_file(incar_filename)["KSPACING"] == 0.48

    # Make second attempt at fixing the error, for when we have the default
    # KSPACING value.
    incar = Incar.from_file(incar_filename)
    incar["KSPACING"] = 0.5
    incar.to_file(incar_filename)
    fix = error_handler.correct(tmp_path)
    assert fix == "switched ISMEAR to 0 and SIGMA to 0.05"
    incar = Incar.from_file(incar_filename)
    assert incar["ISMEAR"] == 0
    assert incar["SIGMA"] == 0.05

    # Confirm an error IS NOT found when there is no vasp.out
    error_handler.filename_to_check = "vasp.does_not_exist"
    assert error_handler.check(tmp_path) == False
