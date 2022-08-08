# -*- coding: utf-8 -*-

from simmate.conftest import copy_test_files, make_dummy_files
from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.workflows.electronic_structure.matproj_band_structure import (
    ElectronicStructure__Vasp__MatprojBandStructure,
)
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS


def test_band_structure_setup(structure, tmpdir, mocker):

    # estabilish filenames that we make and commonly reference
    incar_filename = tmpdir / "INCAR"
    poscar_filename = tmpdir / "POSCAR"
    potcar_filename = tmpdir / "POTCAR"

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # try to make input files in the tmpdir
    ElectronicStructure__Vasp__MatprojBandStructure.setup(
        directory=tmpdir, structure=structure
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


def test_band_structure_workup(tmpdir):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="band_structure.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmpdir / "simmate_summary.yaml"
    plot_filename = tmpdir / "band_structure.png"

    # run the full workup
    ElectronicStructure__Vasp__MatprojBandStructure.workup(tmpdir)
    assert summary_filename.exists()
    assert plot_filename.exists()
