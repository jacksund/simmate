# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.configuration.django.database import reset_database

# reset_database()

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.database.third_parties.scraping.cod import load_all_structures
# test = load_all_structures()

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.database.third_parties.all import MaterialsProjectStructure
from simmate.utilities import get_chemical_subsystems

MaterialsProjectStructure.objects.count()


systems = get_chemical_subsystems("Y-C-F")

MaterialsProjectStructure.objects.filter(chemical_system__in=systems).count()
MaterialsProjectStructure.objects.filter(chemical_system__contains="Y").filter(
    chemical_system__contains="C"
).count()

# --------------------------------------------------------------------------------------

from django.db.models import Sum

MaterialsProjectStructure.objects.aggregate(Sum("nsites"))
