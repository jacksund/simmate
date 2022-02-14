# -*- coding: utf-8 -*-

import pytest

from simmate.database.base_data_types import Spacegroup


@pytest.mark.django_db
def test_spacegroup_table():
    Spacegroup._load_database_from_toolkit()
