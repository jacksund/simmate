# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.diffusion.neb_all_paths_base import (
    NebAllPathsWorkflow,
)
from simmate.calculators.vasp.workflows.diffusion.neb_single_path_mit import (
    Diffusion__Vasp__NebSinglePathMit,
)
from simmate.calculators.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit
from simmate.calculators.vasp.workflows.static_energy.mit import StaticEnergy__Vasp__Mit


class Diffusion__Vasp__NebAllPathsMit(NebAllPathsWorkflow):
    """
    Runs a full diffusion analysis on a bulk crystal structure using NEB with
    MIT settings.
    """

    bulk_relaxation_workflow = Relaxation__Vasp__Mit
    bulk_static_energy_workflow = StaticEnergy__Vasp__Mit
    single_path_workflow = Diffusion__Vasp__NebSinglePathMit
