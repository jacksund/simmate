# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files, make_dummy_files

from simmate.toolkit.diffusion import MigrationImages

from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.tasks.nudged_elastic_band import MITNudgedElasticBand
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)


def test_neb_setup(sample_structures, tmpdir, mocker):

    # To test this task we need to create images, which we do using I diffusion
    # in Y2CI2. We use [0] to grab the shortest path.
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]
    images = MigrationImages.from_structure(structure, "I")[0]

    # estabilish filenames that we make and commonly reference
    incar_filename = os.path.join(tmpdir, "INCAR")
    potcar_filename = os.path.join(tmpdir, "POTCAR")
    # These files exist within a series of directories 00, 01,..., 05
    poscar_filenames = [
        os.path.join(tmpdir, str(n).zfill(2), "POSCAR") for n in range(5)
    ]

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # try to make input files in the tmpdir
    MITNudgedElasticBand.setup(
        migration_images=images,
        directory=tmpdir,
    )
    assert os.path.exists(incar_filename)
    assert os.path.exists(potcar_filename)
    assert all([os.path.exists(f) for f in poscar_filenames])
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
    )


def test_neb_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="nudged_elastic_band",
    )

    # init main task
    task = MITNudgedElasticBand()

    # estabilish filenames that we make and commonly reference
    summary_filename = os.path.join(tmpdir, "simmate_summary.yaml")
    plot_filename = os.path.join(tmpdir, "NEB_plot.jpeg")
    cif_filename = os.path.join(tmpdir, "path_relaxed_neb.cif")

    # run the full workup
    task.workup(tmpdir)
    assert os.path.exists(summary_filename)
    # assert os.path.exists(plot_filename)  # temporarily removed
    assert os.path.exists(cif_filename)
