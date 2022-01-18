# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

from simmate.database.third_parties.aflow import AflowStructure
from simmate.database.third_parties.cod import CodStructure
from simmate.database.third_parties.jarvis import JarvisStructure
from simmate.database.third_parties.materials_project import MatProjStructure
from simmate.database.third_parties.oqmd import OqmdStructure
