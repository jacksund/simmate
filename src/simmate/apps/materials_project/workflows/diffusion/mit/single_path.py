# -*- coding: utf-8 -*-

from simmate.apps.vasp.workflows.diffusion.mit import Diffusion__Vasp__NebFromImagesMit
from simmate.apps.vasp.workflows.diffusion.neb_base import SinglePathWorkflow
from simmate.apps.vasp.workflows.relaxation.mvl_neb_endpoint import (
    Relaxation__Vasp__MvlNebEndpoint,
)
from simmate.apps.vasp.workflows.static_energy import StaticEnergy__Vasp__MvlNebEndpoint


class Diffusion__Vasp__NebSinglePathMit(SinglePathWorkflow):
    """
    Runs a full diffusion analysis on a single migration hop using NEB with
    MIT settings.
    """

    endpoint_relaxation_workflow = Relaxation__Vasp__MvlNebEndpoint
    endpoint_energy_workflow = StaticEnergy__Vasp__MvlNebEndpoint
    from_images_workflow = Diffusion__Vasp__NebFromImagesMit
