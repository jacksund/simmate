# -*- coding: utf-8 -*-

import os

import pytest

from simmate.website.test_app.models import TestForces


@pytest.mark.django_db
def test_forces_table(structure, tmpdir):

    # test writing columns
    TestForces.show_columns()

    # Make up random values for forces and stress. They don't need to be realistic
    example_forces = None  # [[0.5, 0.5, 0.5]] * structure.num_sites
    # example_stress = [
    #     [0.1, 0.1, 0.1],
    #     [0.1, 0.1, 0.1],
    #     [0.1, 0.1, 0.1],
    # ]

    # test writing to database. Note both forces and stress are optional, so
    # we test every iteration of this.
    # structure_db = TestForces.from_toolkit(
    #     structure=structure,
    #     site_forces=example_forces,
    #     lattice_stress=example_stress,
    # )
    # structure_db.save()
    structure_db = TestForces.from_toolkit(
        structure=structure,
        site_forces=example_forces,
    )
    structure_db.save()
    # structure_db = TestForces.from_toolkit(
    #     structure=structure,
    #     lattice_stress=example_stress,
    # )
    # structure_db.save()
    structure_db = TestForces.from_toolkit(
        structure=structure,
    )
    structure_db.save()

    # test writing and reloading these from and archive
    archive_filename = os.path.join(tmpdir, "archive.zip")
    TestForces.objects.to_archive(archive_filename)
    TestForces.load_archive(
        archive_filename,
        confirm_override=True,
        delete_on_completion=True,
    )
