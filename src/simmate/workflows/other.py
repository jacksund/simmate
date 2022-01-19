# -*- coding: utf-8 -*-

# These are tasks that are in early development and don't have databases tables.
# Therefore, they are s3tasks only - not workflows.
from simmate.calculators.vasp.tasks.band_structure import MatProjBandStructure
from simmate.calculators.vasp.tasks.density_of_states import MatProjDensityOfStates
from simmate.calculators.vasp.tasks.dynamics import MITDynamicsTask
from simmate.calculators.vasp.tasks.pre_bader import MatProjPreBaderTask

band_structure_matproj = MatProjBandStructure()
density_of_states_matproj = MatProjDensityOfStates()
dynamics_mit = MITDynamicsTask()
pre_bader_matproj = MatProjPreBaderTask()
