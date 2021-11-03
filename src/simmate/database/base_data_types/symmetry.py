# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from pymatgen.symmetry.groups import SpaceGroup as SpaceGroup_PMG

# NOTE: This class is *not* meant to store data about each spacegroup, but instead
# is just to help with querying Structures. If you want all spacegroup data
# (such as the list of symmetry operations), then you should instead look at
# pymatgen.symmetry.groups.SpaceGroup. There is also spglib where you
# can get data using spglib.get_spacegroup_type(hall_number), but this is organized
# into 530 hall spacegroups, rather than the typical 230 international spacegroups.


class Spacegroup(DatabaseTable):

    """Base Info"""

    # NOTE: International spacegroup info is also known as Hermann-Mauguin

    # International space group number
    number = table_column.IntegerField(primary_key=True)

    # Full international symbol
    symbol = table_column.CharField(max_length=15)

    # The crystal system (don't confused with crystal family or lattice family)
    crystal_system = table_column.CharField(max_length=15)

    # Point group symbol
    point_group = table_column.CharField(max_length=15)

    """ Django App Association """

    class Meta:
        app_label = "third_parties"  # TODO: move to a separate app

    """ Model Methods """

    @staticmethod
    def load_database_from_pymatgen():

        # This method is automatically called when you first set up your
        # Simmate database and should never be called by the user after that.

        for number in range(1, 231):

            # load the pymatgen object that we can easily grab data from
            spacegroup = SpaceGroup_PMG.from_int_number(number)

            # load the data into this django model
            spacegroup_db = Spacegroup(
                number=spacegroup.int_number,
                symbol=spacegroup.symbol,
                crystal_system=spacegroup.crystal_system,
                point_group=spacegroup.point_group,
            )

            # now save this information to the database
            spacegroup_db.save()
