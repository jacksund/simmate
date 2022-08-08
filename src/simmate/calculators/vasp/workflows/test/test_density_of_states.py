# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files
from simmate.calculators.vasp.tasks.density_of_states import MatprojDensityOfStates


def test_density_of_states_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="density_of_states",
    )

    # init main task
    task = MatprojDensityOfStates()

    # estabilish filenames that we make and commonly reference
    summary_filename = os.path.join(tmpdir, "simmate_summary.yaml")
    plot_filename = os.path.join(tmpdir, "density_of_states.png")

    # run the full workup
    task.workup(tmpdir)
    assert os.path.exists(summary_filename)
    assert os.path.exists(plot_filename)
