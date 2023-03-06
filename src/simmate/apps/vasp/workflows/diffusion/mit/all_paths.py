# -*- coding: utf-8 -*-

from simmate.apps.vasp.workflows.diffusion.mit import Diffusion__Vasp__NebSinglePathMit
from simmate.apps.vasp.workflows.diffusion.neb_base import NebAllPathsWorkflow
from simmate.apps.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit
from simmate.apps.vasp.workflows.static_energy.mit import StaticEnergy__Vasp__Mit


class Diffusion__Vasp__NebAllPathsMit(NebAllPathsWorkflow):
    """
    Runs a full diffusion analysis on a bulk crystal structure using NEB with
    MIT settings.
    """

    bulk_relaxation_workflow = Relaxation__Vasp__Mit
    bulk_static_energy_workflow = StaticEnergy__Vasp__Mit
    single_path_workflow = Diffusion__Vasp__NebSinglePathMit
