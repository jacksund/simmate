# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.error_handlers import MeshSymmetry
from simmate.calculators.vasp.inputs import Incar
from simmate.conftest import copy_test_files


def test_mesh_symmetry(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="mesh_symmetry.zip",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = tmp_path / "INCAR"
    kpoints_filename = tmp_path / "KPOINTS"
    vasprun_filename = tmp_path / "vasprun.xml"

    # init class with default settings
    error_handler = MeshSymmetry()

    # Confirm an error IS NOT found when file doesn't exist
    error_handler.filename_to_check = "vasp.does_not_exist"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS NOT found when vasprun.xml is converged
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmp_path) == False

    # Confirm an error IS found when vasprun.xml is not converged
    vasprun_filename.unlink()
    assert error_handler.check(tmp_path) == True

    # Make attempt at fixing the error
    with pytest.raises(NotImplementedError):
        error_handler.correct(tmp_path)

    # Confirm an error IS NOT found when KPOINTS file doesn't exist and KSPACING
    # was set instead.
    kpoints_filename.unlink()
    incar = Incar.from_file(incar_filename)
    incar["KSPACING"] = 0.3
    incar.to_file(incar_filename)
    assert error_handler.check(tmp_path) == False
