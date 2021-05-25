# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.configuration.django.database import reset_database
reset_database()

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.database.third_parties.scraping.materials_project import load_all_structures
# load_all_structures(criteria={"task_id": {"$exists": True}})

# from simmate.shortcuts import setup
# from simmate.database.third_parties.scraping.jarvis import load_all_structures
# load_all_structures()

# from simmate.shortcuts import setup
# from simmate.database.third_parties.scraping.aflow import load_all_structures
# load_all_structures()

from simmate.shortcuts import setup
from simmate.database.third_parties.scraping.oqmd import load_all_structures
load_all_structures()

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.database.third_parties.materials_project import MaterialsProjectStructure
# MaterialsProjectStructure.objects.count()

# from simmate.shortcuts import setup
# from simmate.database.third_parties.jarvis import JarvisStructure
# JarvisStructure.objects.count()

# --------------------------------------------------------------------------------------

