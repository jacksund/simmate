# -*- coding: utf-8 -*-

import os

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.tasks.band_structure import MatprojBandStructure
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS


def test_band_structure_setup(structure, tmpdir, mocker):

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
    MatprojBandStructure.setup(directory=tmpdir, structure=structure)
    assert os.path.exists(incar_filename)
    assert os.path.exists(poscar_filename)
    assert os.path.exists(potcar_filename)
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS,
    )


def test_band_structure_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="band_structure",
    )

    # init main task
    task = MatprojBandStructure()

    # estabilish filenames that we make and commonly reference
    summary_filename = os.path.join(tmpdir, "simmate_summary.yaml")
    plot_filename = os.path.join(tmpdir, "band_structure.png")

    # run the full workup
    task.workup(tmpdir)
    assert os.path.exists(summary_filename)
    assert os.path.exists(plot_filename)
