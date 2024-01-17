# -*- coding: utf-8 -*-

from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow
from simmate.apps.vasp.workflows.diffusion import (
    NebAllPathsWorkflow,
    SinglePathWorkflow,
    VaspNebFromImagesWorkflow,
)

# -----------------------------------------------------------------------------

# BULK UNITCELL RELAXATION


class Relaxation__Vasp__WarrenLabQuick(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=1e-05,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=2,
        ICHARG=1,
        ISIF=3,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.5,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# BULK UNITCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLabQuick(Relaxation__Vasp__WarrenLabQuick):
    _incar_updates = dict(IBRION=-1, NSW=0)


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL RELAXATIONS


class Relaxation__Vasp__WarrenLabQuickNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=5e-04,
        EDIFFG=-0.02,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=2,
        ICHARG=1,
        ISIF=2,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        LCHARG=False,
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.5,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLabQuickNebEndpoint(
    Relaxation__Vasp__WarrenLabQuickNebEndpoint
):
    _incar_updates = dict(IBRION=-1, NSW=0)


# -----------------------------------------------------------------------------

# NEB FROM IMAGES


class Diffusion__Vasp__WarrenLabQuickCiNebFromImages(VaspNebFromImagesWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=5e-04,
        EDIFFG=-0.02,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=3,
        ICHARG=1,
        ISIF=2,
        ISPIN=2,
        ISYM=0,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        LCHARG=False,
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.5,
        LMAXMIX=4,
        IMAGES=3,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# SINGLE PATH NEB


class Diffusion__Vasp__WarrenLabQuickNebSinglePath(SinglePathWorkflow):
    endpoint_relaxation_workflow = Relaxation__Vasp__WarrenLabQuickNebEndpoint
    endpoint_energy_workflow = StaticEnergy__Vasp__WarrenLabQuickNebEndpoint
    from_images_workflow = Diffusion__Vasp__WarrenLabQuickCiNebFromImages


# -----------------------------------------------------------------------------

# ALL PATHS NEB


class Diffusion__Vasp__NebAllPathsWarrenLabQuick(NebAllPathsWorkflow):
    bulk_relaxation_workflow = Relaxation__Vasp__WarrenLabQuick
    bulk_static_energy_workflow = StaticEnergy__Vasp__WarrenLabQuick
    single_path_workflow = Diffusion__Vasp__WarrenLabQuickNebSinglePath


# -----------------------------------------------------------------------------
