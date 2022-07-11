# -*- coding: utf-8 -*-

# I store all of my models elsewhere, so this file simply exists to show django where
# they are located at. I do this based on the directions given by:
# https://docs.djangoproject.com/en/3.1/topics/db/models/#organizing-models-in-a-package

from simmate.database.third_parties import (
    MatprojStructure,
    JarvisStructure,
    AflowStructure,
    AflowPrototype,
    OqmdStructure,
    CodStructure,
)
