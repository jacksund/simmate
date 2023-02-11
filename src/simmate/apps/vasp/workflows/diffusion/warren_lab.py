# -*- coding: utf-8 -*-

from simmate.apps.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow
from simmate.apps.vasp.workflows.diffusion.neb_base import (
    NebAllPathsWorkflow,
    SinglePathWorkflow,
    VaspNebFromImagesWorkflow,
)

# -----------------------------------------------------------------------------

# BULK UNITCELL RELAXATION


class Relaxation__Vasp__WarrenLab(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS
    incar = dict(
        ALGO="Normal",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        IVDW=12,
        # ... I just typed some random settings here. Update these to your liking
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# BULK UNITCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLab(Relaxation__Vasp__WarrenLab):
    incar = Relaxation__Vasp__WarrenLab.incar.copy()
    incar.update(dict(IBRION=-1, NSW=0))


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL RELAXATIONS


class Relaxation__Vasp__WarrenLabNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        ISIF=2,
        # ... I just typed some random settings here. Update these to your liking
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLabNebEndpoint(Relaxation__Vasp__WarrenLabNebEndpoint):
    incar = Relaxation__Vasp__WarrenLabNebEndpoint.incar.copy()
    incar.update(dict(IBRION=-1, NSW=0))


# -----------------------------------------------------------------------------

# NEB FROM IMAGES


class Diffusion__Vasp__WarrenLabCiNebFromImages(VaspNebFromImagesWorkflow):
    incar = Relaxation__Vasp__WarrenLabNebEndpoint.incar.copy()
    incar.update(
        dict(
            ISYM=0,
            LCHARG=False,
            IMAGES__auto=True,
            LCLIMB=True,
            POTIM=0,
            IBRION=3,
            IOPT=1,
            # ... I just typed some random settings here. Update these to your liking
        )
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# SINGLE PATH NEB


class Diffusion__Vasp__WarrenLabNebSinglePath(SinglePathWorkflow):
    endpoint_relaxation_workflow = Relaxation__Vasp__WarrenLabNebEndpoint
    endpoint_energy_workflow = StaticEnergy__Vasp__WarrenLabNebEndpoint
    from_images_workflow = Diffusion__Vasp__WarrenLabCiNebFromImages


# -----------------------------------------------------------------------------

# ALL PATHS NEB


class Diffusion__Vasp__NebAllPathsMit(NebAllPathsWorkflow):
    bulk_relaxation_workflow = Relaxation__Vasp__WarrenLab
    bulk_static_energy_workflow = StaticEnergy__Vasp__WarrenLab
    single_path_workflow = Diffusion__Vasp__WarrenLabNebSinglePath


# -----------------------------------------------------------------------------
