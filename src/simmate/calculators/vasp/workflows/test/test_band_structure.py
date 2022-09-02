# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.conftest import SimmateMockHelper, copy_test_files


def test_band_structure_setup(structure, tmp_path, mocker):

    Potcar = SimmateMockHelper.get_mocked_potcar(mocker, tmp_path)

    # estabilish filenames that we make and commonly reference
    incar_filename = tmp_path / "INCAR"
    poscar_filename = tmp_path / "POSCAR"
    potcar_filename = tmp_path / "POTCAR"

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


@pytest.mark.django_db
def test_band_structure_run(sample_structures, tmp_path, mocker):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="band_structure.zip",
    )

    SimmateMockHelper.mock_vasp(mocker)

    # run the full workflow, where the output files were pre-generated with
    # a specific structures
    structure = sample_structures["Fe_mp-13_primitive"]
    ElectronicStructure__Vasp__MatprojBandStructure.run(
        structure=structure,
        directory=tmp_path,
    )

    # check output files
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / "band_diagram.png"
    assert summary_filename.exists()
    assert plot_filename.exists()
