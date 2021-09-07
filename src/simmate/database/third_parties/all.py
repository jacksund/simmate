# -*- coding: utf-8 -*-

# This file sets up a shortcut for importing so that you can do...
#
#   from simmate.database.third_parties.all import (
#       MaterialsProjectStructure,
#       JarvisStructure,
#       AflowStructure,
#       OqmdStructure,
#       OcdStructure,
#   )
#
# instead of what's written below. You should only use this shortcut if you are
# using ALL of the classes below or if you are running some quick interactive test.

from simmate.database.third_parties.materials_project import MaterialsProjectStructure
from simmate.database.third_parties.jarvis import JarvisStructure
from simmate.database.third_parties.aflow import AflowStructure
from simmate.database.third_parties.oqmd import OqmdStructure
from simmate.database.third_parties.cod import CodStructure
