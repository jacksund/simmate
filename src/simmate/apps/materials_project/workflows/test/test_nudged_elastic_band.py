# -*- coding: utf-8 -*-

import pytest

from simmate.apps.materials_project.workflows.diffusion import (
    Diffusion__Vasp__NebAllPathsMit,
    Diffusion__Vasp__NebFromImagesMit,
)
from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS_LOW_QUALITY
from simmate.conftest import SimmateMockHelper, copy_test_files
from simmate.toolkit.diffusion import MigrationImages


@pytest.mark.slow
@pytest.mark.django_db
def test_neb_all_paths(sample_structures, tmp_path, mocker):
    SimmateMockHelper.mock_vasp(mocker)
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="nudged_elastic_band.zip",
    )

    # For testing, look at I- diffusion in Y2CF2
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]

    # run the workflow and make sure it handles data properly.
    state = Diffusion__Vasp__NebAllPathsMit.run(
        structure=structure,
        migrating_specie="I",
        # command="dummycmd1; dummycmd2; dummycmd3",
        directory=tmp_path,
    )
    assert state.is_completed()

    # estabilish filenames that we make and commonly reference
    path_dir = "diffusion.vasp.neb-single-path-mit.00"
    summary_filename = tmp_path / "simmate_summary.yaml"
    plot_filename = tmp_path / path_dir / "neb_diagram.png"
    cif_filename = tmp_path / path_dir / "simmate_path_relaxed_neb.cif"

    # run the full workup
    assert summary_filename.exists()
    assert plot_filename.exists()
    assert cif_filename.exists()


def test_neb_from_images_setup(sample_structures, tmp_path, mocker):
    Potcar = SimmateMockHelper.get_mocked_potcar(mocker, tmp_path)

    # To test this task we need to create images, which we do using I diffusion
    # in Y2CI2. We use [0] to grab the shortest path.
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]
    images = MigrationImages.from_structure(structure, "I")[0]

    # estabilish filenames that we make and commonly reference
    incar_filename = tmp_path / "INCAR"
    potcar_filename = tmp_path / "POTCAR"
    # These files exist within a series of directories 00, 01,..., 05
    poscar_filenames = [tmp_path / str(n).zfill(2) / "POSCAR" for n in range(5)]

    # try to make input files in the tmp_path
    Diffusion__Vasp__NebFromImagesMit.setup(
        migration_images=images,
        directory=tmp_path,
    )
    assert incar_filename.exists()

    assert all([f.exists() for f in poscar_filenames])

    assert potcar_filename.exists()
    Potcar.to_file_from_type.assert_called_with(
        structure.composition.elements,
        "PBE",
        potcar_filename,
        PBE_POTCAR_MAPPINGS_LOW_QUALITY,
    )
