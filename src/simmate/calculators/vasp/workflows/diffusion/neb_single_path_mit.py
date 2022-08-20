# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.diffusion.neb_from_images_mit import (
    Diffusion__Vasp__NebFromImagesMit,
)
from simmate.calculators.vasp.workflows.diffusion.neb_single_path_base import (
    SinglePathWorkflow,
)
from simmate.calculators.vasp.workflows.relaxation.mvl_neb_endpoint import (
    Relaxation__Vasp__MvlNebEndpoint,
)


class Diffusion__Vasp__NebSinglePathMit(SinglePathWorkflow):
    """
    Runs a full diffusion analysis on a single migration hop using NEB with
    MIT settings.
    """

    endpoint_relaxation_workflow = Relaxation__Vasp__MvlNebEndpoint
    from_images_workflow = Diffusion__Vasp__NebFromImagesMit
