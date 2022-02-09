# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import TestThermodynamics


@pytest.mark.django_db
def test_thermo_table(structure):

    # test writing columns
    TestThermodynamics.show_columns()

    # test writing to database
    structure_db = TestThermodynamics.from_toolkit(
        structure=structure,
        energy=-1.23,
    )
    structure_db.save()
    structure_db2 = TestThermodynamics.from_toolkit(
        structure=structure,
        energy=-4.56,
    )
    structure_db2.save()

    # test updating stabilites, even though our table is basically empty.
    TestThermodynamics.update_all_stabilities()

    # For some compositions where endpoints aren't in the database, this
    # underlying methods should be tested.
    # with pytest.raises(ValueError):
    #     TestThermodynamics.update_chemical_system_stabilities(
    #         structure_db.chemical_system,
    #     )

    # test writing and reloading these from and archive
    TestThermodynamics.objects.to_archive()
    TestThermodynamics.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )
