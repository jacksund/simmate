# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

from simmate.configuration.django import setup_full  # sets database connection

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
from simmate.calculators.vasp.tasks.band_structure import MatProjBandStructure

band_structure_matproj = MatProjBandStructure()

from simmate.calculators.vasp.tasks.density_of_states import MatProjDensityOfStates

density_of_states_matproj = MatProjDensityOfStates()
