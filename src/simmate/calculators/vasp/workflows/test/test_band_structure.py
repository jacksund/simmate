# -*- coding: utf-8 -*-

from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.conftest import copy_test_files, make_dummy_files


def test_band_structure_setup(structure, tmp_path, mocker):

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
    ElectronicStructure__Vasp__MatprojBandStructure.setup(
        directory=tmp_path, structure=structure
    )
    assert incar_filename.exists()
    assert poscar_filename.exists()
    assert potcar_filename.exists()
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS,
    )


def test_band_structure_workup(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="band_structure.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / "band_structure.png"

    # run the full workup
    ElectronicStructure__Vasp__MatprojBandStructure.workup(tmp_path)
    assert summary_filename.exists()
    assert plot_filename.exists()
