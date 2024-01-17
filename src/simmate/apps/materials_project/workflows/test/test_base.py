# -*- coding: utf-8 -*-

import pytest

from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow
from simmate.conftest import SimmateMockHelper, copy_test_files


class Testing__Vasp__Dummy(VaspWorkflow):
    """
    A minimal example VaspWorkflow that is just for testing
    """

    use_database = False

    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    standardize_structure = "primitive-LLL"
    symmetry_tolerance = 0.1
    angle_tolerance = 10.0

    _incar = dict(
        PREC="Low",
        EDIFF__per_atom=2e-3,  # to ensure structure-specific kwargs
        KSPACING=0.75,
    )


# For shorthand reference below
DummyWorkflow = Testing__Vasp__Dummy


def test_base_setup(structure, tmp_path, mocker):
    Potcar = SimmateMockHelper.get_mocked_potcar(mocker, tmp_path)

    # estabilish filenames that we make and commonly reference
    incar_filename = tmp_path / "INCAR"
    poscar_filename = tmp_path / "POSCAR"
    potcar_filename = tmp_path / "POTCAR"

    # try to make input files in the tmp_path
    DummyWorkflow.setup(directory=tmp_path, structure=structure)
    assert incar_filename.exists()
    assert poscar_filename.exists()
    assert potcar_filename.exists()
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_POTCAR_MAPPINGS,
    )


def test_base_vasp_run(structure, tmp_path, mocker):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="base.zip",
    )

    SimmateMockHelper.mock_vasp(mocker)

    # estabilish filenames that we make and commonly reference
    vasprun_filename = tmp_path / "vasprun.xml"

    # run the full workflow
    DummyWorkflow.run(structure=structure, directory=tmp_path)

    # run the workup again with a malformed xml
    with vasprun_filename.open("r") as file:
        contents = file.readlines()
    with vasprun_filename.open("w") as file:
        file.writelines(contents[50])
    with pytest.raises(Exception):
        DummyWorkflow.run(tmp_path)
