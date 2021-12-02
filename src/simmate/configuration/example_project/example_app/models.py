# -*- coding: utf-8 -*-

"""
This is where you add any new database tables you'd like. This file is named
"models.py" because that what Django expects! In their terminology, a django 
model is the same thing as a database table.

As an example here, we set up tables for a VASP relaxation. There are two tables
here: one for the relaxations and a second for storing each ionic step in the 
relaxation.

Note that we use IonicStepStructure and Relaxation classes to inherit from.
This let's us automatically add useful columns and features -- so you don't have
to add everything from scratch. The only code that we write here simply connects
these database tables and/or adds new custom columns.
"""

from simmate.database.local_calculations.relaxation.base import Relaxation

MITRelaxation, MITIonicStep = Relaxation.create_all_subclasses("MIT", module=__name__)
