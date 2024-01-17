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


class Relaxation__Vasp__WarrenLab(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=1e-06,
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
        # MAGMOM = # TODO: set dynamically
        NELM=200,
        NELMIN=4,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.35,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# BULK UNITCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLab(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=1e-06,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=-1,
        ICHARG=1,
        ISIF=3,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        # MAGMOM = # TODO: set dynamically
        NELM=200,
        NELMIN=4,
        NSW=0,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.35,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL RELAXATIONS


class Relaxation__Vasp__WarrenLabNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
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
        # MAGMOM = # TODO: set dynamically
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.4,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLabNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=-1,
        ICHARG=1,
        ISIF=2,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        LCHARG=False,
        # MAGMOM = # TODO: set dynamically
        NELM=200,
        NSW=0,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.4,
        LMAXMIX=4,
    )
    error_handlers = []


# -----------------------------------------------------------------------------

# NEB FROM IMAGES


class Diffusion__Vasp__WarrenLabCiNebFromImages(VaspNebFromImagesWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
        ENCUT=520,  # TODO: set dynamically to be 1.3x highest elemental ENMAX
        IBRION=3,
        ICHARG=1,
        ISIF=2,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        LCHARG=False,
        # MAGMOM = # TODO: set dynamically
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.4,
        LMAXMIX=4,
        NIMAGES__auto=True,  # set by simmate
        LCLIMB=True,
        SPRING=-5,
        POTIM=0,
        IOPT=1,
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


class Diffusion__Vasp__NebAllPathsWarrenLab(NebAllPathsWorkflow):
    bulk_relaxation_workflow = Relaxation__Vasp__WarrenLab
    bulk_static_energy_workflow = StaticEnergy__Vasp__WarrenLab
    single_path_workflow = Diffusion__Vasp__WarrenLabNebSinglePath


# -----------------------------------------------------------------------------
