# -*- coding: utf-8 -*-

# TODO: when I add more calculators, I can do something like this...
# if "simmate.calculators.vasp" in installed_apps:
from simmate.calculators.vasp.workflows.energy.all import (
    energy_mit,
    energy_quality04,
    energy_matproj,
)
from simmate.calculators.vasp.workflows.relaxation.all import (
    relaxation_mit,
    relaxation_matproj,
    relaxation_quality00,
    relaxation_quality01,
    relaxation_quality02,
    relaxation_quality03,
    relaxation_quality04,
    relaxation_staged,
)

# These are tasks that are in early development and don't have databases tables.
# Therefore, they are s3tasks only - not workflows.
from simmate.calculators.vasp.tasks.band_structure import (
    MaterialsProjectBandStructureTask as band_structure_matproj,
)
from simmate.calculators.vasp.tasks.density_of_states import (
    MaterialsProjectDensityOfStatesTask as density_of_states_matproj,
)
