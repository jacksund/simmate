# -*- coding: utf-8 -*-

import os
import pytest

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.error_handlers import MeshSymmetry


def test_mesh_symmetry(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="mesh_symmetry",
    )

    # we reference the files several spots below so we grab its path up front
    incar_filename = os.path.join(tmpdir, "INCAR")
    kpoints_filename = os.path.join(tmpdir, "KPOINTS")
    vasprun_filename = os.path.join(tmpdir, "vasprun.xml")

    # init class with default settings
    error_handler = MeshSymmetry()

    # Confirm an error IS NOT found when file doesn't exist
    error_handler.filename_to_check = "vasp.does_not_exist"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS NOT found when vasprun.xml is converged
    error_handler.filename_to_check = "vasp.out"
    assert error_handler.check(tmpdir) == False

    # Confirm an error IS found when vasprun.xml is not converged
    os.remove(vasprun_filename)
    assert error_handler.check(tmpdir) == True

    # Make attempt at fixing the error
    with pytest.raises(NotImplementedError):
        error_handler.correct(tmpdir)

    # Confirm an error IS NOT found when KPOINTS file doesn't exist and KSPACING
    # was set instead.
    os.remove(kpoints_filename)
    incar = Incar.from_file(incar_filename)
    incar["KSPACING"] = 0.3
    incar.to_file(incar_filename)
    assert error_handler.check(tmpdir) == False
