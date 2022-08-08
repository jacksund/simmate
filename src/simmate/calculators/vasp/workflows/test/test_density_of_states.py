# -*- coding: utf-8 -*-

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.workflows.electronic_structure.matproj_density_of_states import (
    ElectronicStructure__Vasp__MatprojDensityOfStates,
)


def test_density_of_states_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="density_of_states.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmpdir / "simmate_summary.yaml"
    plot_filename = tmpdir / "density_of_states.png"

    # run the full workup
    ElectronicStructure__Vasp__MatprojDensityOfStates.workup(tmpdir)
    assert summary_filename.exists()
    assert plot_filename.exists()
