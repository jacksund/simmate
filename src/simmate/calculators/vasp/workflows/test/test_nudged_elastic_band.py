# -*- coding: utf-8 -*-

from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)
from simmate.calculators.vasp.workflows.diffusion.neb_from_images_mit import (
    Diffusion__Vasp__NebFromImagesMit,
)
from simmate.conftest import copy_test_files, make_dummy_files
from simmate.toolkit.diffusion import MigrationImages


def test_neb_setup(sample_structures, tmp_path, mocker):

    # To test this task we need to create images, which we do using I diffusion
    # in Y2CI2. We use [0] to grab the shortest path.
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]
    images = MigrationImages.from_structure(structure, "I")[0]

    # estabilish filenames that we make and commonly reference
    incar_filename = tmp_path / "INCAR"
    potcar_filename = tmp_path / "POTCAR"
    # These files exist within a series of directories 00, 01,..., 05
    poscar_filenames = [tmp_path / str(n).zfill(2) / "POSCAR" for n in range(5)]

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(
        Potcar,
        "to_file_from_type",
        return_value=make_dummy_files(potcar_filename),
    )

    # try to make input files in the tmp_path
    Diffusion__Vasp__NebFromImagesMit.setup(
        migration_images=images,
        directory=tmp_path,
    )
    assert incar_filename.exists()
    assert potcar_filename.exists()
    assert all([f.exists() for f in poscar_filenames])
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
    )


def test_neb_workup(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="nudged_elastic_band.zip",
    )

    # estabilish filenames that we make and commonly reference
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / "NEB_plot.jpeg"
    cif_filename = tmp_path / "path_relaxed_neb.cif"

    # run the full workup
    Diffusion__Vasp__NebFromImagesMit.workup(tmp_path)
    assert summary_filename.exists()
    # assert os.path.exists(plot_filename)  # temporarily removed
    assert cif_filename.exists()
