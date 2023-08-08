# -*- coding: utf-8 -*-

from pymatgen.symmetry.groups import SpaceGroup as PymatgenSpacegroup
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column

# NOTE: This class is *not* meant to store data about each spacegroup, but instead
# is just to help with querying Structures. If you want all spacegroup data
# (such as the list of symmetry operations), then you should instead look at
# pymatgen.symmetry.groups.SpaceGroup. There is also spglib where you
# can get data using spglib.get_spacegroup_type(hall_number), but this is organized
# into 530 hall spacegroups, rather than the typical 230 international spacegroups.


class Spacegroup(DatabaseTable):
    class Meta:
        app_label = "core_components"

    api_filters = dict(
        number=["exact", "range"],
        symbol=["exact"],
        crystal_system=["exact"],
        point_group=["exact"],
    )

    id = None
    source = None
    """
    The source column is disabled for this table because this is common
    information.
    """

    # NOTE: International spacegroup info is also known as Hermann-Mauguin

    number = table_column.IntegerField(primary_key=True)
    """
    International space group number
    """

    symbol = table_column.CharField(max_length=15)
    """
    Full international symbol
    """

    crystal_system = table_column.CharField(max_length=15)
    """
    The crystal system (don't confused with crystal family or lattice family)
    """

    point_group = table_column.CharField(max_length=15)
    """
    Point group symbol
    """

    @classmethod
    def _load_database_from_toolkit(cls):
        """
        Loads spacegroup data into the database table.

        This should never be called by the user. This method is automatically
        called when you first set up your database and should never be called
        after that.

        See `simmate.database.utilities.reset_database`
        """

        db_objects = []
        for number in track(range(1, 231)):
            # reverse() is 100% not needed but is nice for users to see progress
            # get faster instead of slower.
            number = 231 - number

            # load the pymatgen object that we can easily grab data from
            spacegroup = PymatgenSpacegroup.from_int_number(number)

            # load the data into this django model
            spacegroup_db = cls(
                number=spacegroup.int_number,
                symbol=spacegroup.symbol,
                crystal_system=spacegroup.crystal_system,
                point_group=spacegroup.point_group,
            )
            db_objects.append(spacegroup_db)

        # now save this information to the database
        cls.objects.bulk_create(db_objects, ignore_conflicts=True)
