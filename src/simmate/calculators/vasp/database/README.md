VASP Database Tables
--------------------

This module defines the database tables where VASP workflow results are stored. Because results are of standard types (such as from a relaxation or static energy calculation), this module contains very little code. Building the tables only involved inheriting from mix-ins in the `simmate.database.base_data_types` module.
