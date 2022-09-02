# -*- coding: utf-8 -*-

import pytest

from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.conftest import SimmateMockHelper, copy_test_files


@pytest.mark.django_db
def test_density_of_states_run(sample_structures, tmp_path, mocker):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="band_structure.zip",
    )

    SimmateMockHelper.mock_vasp(mocker)

    # run the full workflow, where the output files were pre-generated with
    # a specific structures
    structure = sample_structures["Fe_mp-13_primitive"]
    ElectronicStructure__Vasp__MatprojDensityOfStates.run(
        structure=structure,
        directory=tmp_path,
    )

    # check output files
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / "dos_diagram.png"
    assert summary_filename.exists()
    assert plot_filename.exists()
