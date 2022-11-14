# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 11:34:18 2022

@author: siona
"""

from simmate.workflow_engine import S3Workflow


class MlPotential__Deepmd__FreezeModel(S3Workflow):

    use_database = False
    command = "dp freeze -o graph.pb"