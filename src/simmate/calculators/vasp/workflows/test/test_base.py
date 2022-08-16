# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.base import VaspWorkflow
from simmate.conftest import copy_test_files, make_dummy_files


class Testing__Vasp__Dummy(VaspWorkflow):
    """
    A minimal example VaspWorkflow that is just for testing
    """

    use_database = False

    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS
    confirm_convergence = True
    pre_sanitize_structure = True
    incar = dict(
        PREC="Low",
        EDIFF__per_atom=2e-3,  # to ensure structure-specific kwargs
        KSPACING=0.75,
    )


# For shorthand reference below
DummyWorkflow = Testing__Vasp__Dummy


def test_base_setup(structure, tmp_path, mocker):

    # estabilish filenames that we make and commonly reference
    incar_filename = tmp_path / "INCAR"
    poscar_filename = tmp_path / "POSCAR"
    potcar_filename = tmp_path / "POTCAR"

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # try to make input files in the tmp_path
    DummyWorkflow.setup(directory=tmp_path, structure=structure)
    assert incar_filename.exists()
    assert poscar_filename.exists()
    assert potcar_filename.exists()
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS,
    )


def test_base_workup(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="base.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmp_path / "simmate_summary.yaml"
    vasprun_filename = tmp_path / "vasprun.xml"

    # run the full workup
    DummyWorkflow.workup(tmp_path)
    assert summary_filename.exists()

    # run the workup again with a malformed xml
    with vasprun_filename.open("r") as file:
        contents = file.readlines()
    with vasprun_filename.open("w") as file:
        file.writelines(contents[50])
    with pytest.raises(Exception):
        DummyWorkflow.workup(tmp_path)
