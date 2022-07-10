# -*- coding: utf-8 -*-

import os

import pytest

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS


class DummyTask(VaspTask):
    """
    A minimal example VaspTask that is just for testing
    """

    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS
    confirm_convergence = True
    pre_sanitize_structure = True
    incar = dict(
        PREC="Low",
        EDIFF__per_atom=2e-3,  # to ensure structure-specific kwargs
        KSPACING=0.75,
    )


def test_base_setup(structure, tmpdir, mocker):

    # estabilish filenames that we make and commonly reference
    incar_filename = os.path.join(tmpdir, "INCAR")
    poscar_filename = os.path.join(tmpdir, "POSCAR")
    potcar_filename = os.path.join(tmpdir, "POTCAR")

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # try to make input files in the tmpdir
    DummyTask.setup(directory=tmpdir, structure=structure)
    assert os.path.exists(incar_filename)
    assert os.path.exists(poscar_filename)
    assert os.path.exists(potcar_filename)
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS,
    )


def test_base_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="base",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = os.path.join(tmpdir, "simmate_summary.yaml")
    vasprun_filename = os.path.join(tmpdir, "vasprun.xml")

    # run the full workup
    DummyTask.workup(tmpdir)
    assert os.path.exists(summary_filename)

    # run the workup again with a malformed xml
    with open(vasprun_filename, "r") as file:
        contents = file.readlines()
    with open(vasprun_filename, "w") as file:
        file.writelines(contents[50])
    with pytest.raises(Exception):
        DummyTask.workup(tmpdir)
