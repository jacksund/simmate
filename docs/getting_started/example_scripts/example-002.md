
# Example 002

## About :star:

This script queries the Material Project database for all ZnSnF6 structures with spacegroup=148 and then runs a (i) relaxation, (ii) static-energy, and (iii) bandstructure + density of states calculation on each -- passing the results between each step.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Becca Radomsky                             |
| Github User     | [@becca9835](https://github.com/becca9835) |
| Last updated    | 2023.05.31                                 |
| Simmate Version | v0.13.2                                    |

## Prerequisites :rotating_light:

- [x] Simmate configured with default settings will work!
- [x] In the script below, go through and replace everywhere you see `write out the rest of your settings`. This file can be used as an example for common settings.
- [x] The NEB settings below use CI-NEB, which requires some of the [VTST-tools](https://theory.cm.utexas.edu/vtsttools/neb.html) installed. You modify these settings to just use a normal VASP NEB run if you'd like (see the comment `Modify these if you don't want CI-NEB`).


## The script :rocket:

!!! info
    Run this script where you'd like the VASP calculations to run!

    The script can be called with something like `python myscript.py` and
    this line can be on your desktop, inside a SLURM job, or whereever!

``` python
# -*- coding: utf-8 -*-

from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
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
    potcar_mappings = PBE_POTCAR_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF=1e-06,
        ENCUT=520,
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
        NELMIN=4,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.35,
        LMAXMIX=4,
    )


# -----------------------------------------------------------------------------

# BULK UNITCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLab(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF=1e-06,
        ENCUT=520,
        IBRION=-1,
        ICHARG=1,
        ISIF=3,
        ISPIN=2,
        ISYM=0,
        IVDW=12,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=200,
        NELMIN=4,
        NSW=0,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.35,
        LMAXMIX=4,
    )


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL RELAXATIONS


class Relaxation__Vasp__WarrenLabNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
        ENCUT=520,
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
        KSPACING=0.4,
        LMAXMIX=4,
    )


# -----------------------------------------------------------------------------

# ENDPOINT SUPERCELL STATIC ENERGY


class StaticEnergy__Vasp__WarrenLabNebEndpoint(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
        ENCUT=520,
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
        NELM=200,
        NSW=0,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.4,
        LMAXMIX=4,
    )


# -----------------------------------------------------------------------------

# NEB FROM IMAGES


class Diffusion__Vasp__WarrenLabCiNebFromImages(VaspNebFromImagesWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    incar = dict(
        ALGO="Fast",
        EDIFF=5e-05,
        EDIFFG=-0.01,
        ENCUT=520,
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
        NELM=200,
        NSW=99,
        PREC="Accurate",
        ISMEAR=0,
        SIGMA=0.05,
        KSPACING=0.4,
        LMAXMIX=4,
        NIMAGES__auto=True,  # set automatically by simmate
        # Modify these if you don't want CI-NEB
        LCLIMB=True,
        SPRING=-5,
        POTIM=0,
        IOPT=1,
    )


# -----------------------------------------------------------------------------
# The two sections below use Simmate to piece together our individual
# VASP calculations above.
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
# Now that we have our new & custom NEB workflow, we can run that
# full workflow analysis. Here, we just run it locally and one vasp calc
# at a time.
# -----------------------------------------------------------------------------

# now run the workflow!
result = Diffusion__Vasp__NebAllPathsWarrenLab.run(
    structure="example.cif",
    migrating_specie="Li",
    command="mpirun -n 10 vasp_std > vasp.out",  # make sure -n is divisible by nimages!
    # Then any extra optional settings below.
    # These parameters are automatically available thanks
    # to the configuration we did above.
    relax_bulk=True,
    relax_endpoints=True,
    nimages=5,
    min_supercell_atoms=80,
    max_supercell_atoms=240,
    min_supercell_vector_lengths=10,
    max_path_length=5,
    percolation_mode=">1d",
    vacancy_mode=True,
)
```
