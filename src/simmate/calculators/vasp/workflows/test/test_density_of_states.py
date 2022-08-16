# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)
from simmate.conftest import copy_test_files


def test_density_of_states_workup(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="density_of_states.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / "density_of_states.png"

    # run the full workup
    ElectronicStructure__Vasp__MatprojDensityOfStates.workup(tmp_path)
    assert summary_filename.exists()
    assert plot_filename.exists()
