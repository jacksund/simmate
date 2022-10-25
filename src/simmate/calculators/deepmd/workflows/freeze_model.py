# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 11:34:18 2022

@author: siona
"""

from simmate.workflow_engine import Workflow


class MlPotential__Deepmd__Freeze(Workflow):
    
    use_database = False
    command = 'dp freeze -o graph.pb' #!!!might have to compress model before using
    
    