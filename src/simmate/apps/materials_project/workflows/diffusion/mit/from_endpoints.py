# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.diffusion.mit import (
    Diffusion__Vasp__NebFromImagesMit,
)
from simmate.apps.materials_project.workflows.relaxation.mvl_neb_endpoint import (
    Relaxation__Vasp__MvlNebEndpoint,
)
from simmate.apps.vasp.workflows.diffusion import NebFromEndpointWorkflow


class Diffusion__Vasp__NebFromEndpointsMit(NebFromEndpointWorkflow):
    """
    Runs a full diffusion analysis from a start and end supercell using NEB with
    MIT settings.
    """

    endpoint_relaxation_workflow = Relaxation__Vasp__MvlNebEndpoint
    from_images_workflow = Diffusion__Vasp__NebFromImagesMit
