# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.diffusion.neb_from_endpoints_base import (
    NebFromEndpointWorkflow,
)
from simmate.calculators.vasp.workflows.diffusion.neb_from_images_mit import (
    Diffusion__Vasp__NebFromImagesMit,
)
from simmate.calculators.vasp.workflows.relaxation.mvl_neb_endpoint import (
    Relaxation__Vasp__MvlNebEndpoint,
)


class Diffusion__Vasp__NebFromEndpointsMit(NebFromEndpointWorkflow):
    """
    Runs a full diffusion analysis from a start and end supercell using NEB with
    MIT settings.
    """

    endpoint_relaxation_workflow = Relaxation__Vasp__MvlNebEndpoint
    from_images_workflow = Diffusion__Vasp__NebFromImagesMit
