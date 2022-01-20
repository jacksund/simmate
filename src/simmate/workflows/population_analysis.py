# -*- coding: utf-8 -*-

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:

# These are tasks that are in early development and don't have databases tables.
# Therefore, they are s3tasks only - not workflows.
from simmate.calculators.vasp.tasks.pre_bader import MatProjPreBaderTask

matproj_workflow = MatProjPreBaderTask()
