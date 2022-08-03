# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)
from simmate.calculators.vasp.error_handlers import (
    TetrahedronMesh,
    RotationMatrix,
    Brmix,
    Zpotrf,
    SubspaceMatrix,
    IncorrectShift,
    RealOptlay,
    Tetirr,
    RotationNonIntMatrix,
    LongVector,
    TripleProduct,
    Pricel,
    Brions,
    Zbrent,
    InsufficientBands,
    Pssyevx,
    Eddrmm,
    Edddav,
    Edwav,
    Zheev,
    ElfKpar,
    Rhosyg,
    Posmap,
    PointGroup,
    SymprecNoise,
    IncorrectSmearing,
    MeshSymmetry,
    Unconverged,
    NonConverging,
    Potim,
    PositiveEnergy,
    Frozen,
    LargeSigma,
    Walltime,
)


class MITRelaxation(VaspTask):
    """
    This task is a reimplementation of pymatgen's
    [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet).

    Runs a VASP geometry optimization using MIT Project settings, where the
    MIT Project is the precursor to the Materials Project.

    From their documention in pymatgen:
    ```
    Default VASP settings for calculations in the pre-cursor MIT project to
    the Materials Project. Reasonably robust, but selected PSP are generally the
    ones with fewer electrons and convergence criteria is less tight. This was
    used in an era whether computational power is more limited.
    Nevertheless, this is still a good starting point for extremely expensive
    methods.
    ```
    """

    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY

    incar = dict(
        ALGO="Fast",
        EDIFF=1.0e-05,
        ENCUT=520,
        IBRION=2,
        ICHARG=1,
        ISIF=3,
        ISPIN=2,
        ISYM=0,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=200,
        NELMIN=6,
        NSW=99,
        PREC="Accurate",
        ISMEAR=-5,
        SIGMA=0.05,
        KSPACING=0.5,  # !!! This is where we are different from pymatgen right now
        MAGMOM__smart_magmom={
            "default": 0.6,  # note this is different from the VASP default
            "Ce": 5,
            "Ce3+": 1,
            "Co": 0.6,
            "Co3+": 0.6,
            "Co4+": 1,
            "Cr": 5,
            "Dy3+": 5,
            "Er3+": 3,
            "Eu": 10,
            "Eu2+": 7,
            "Eu3+": 6,
            "Fe": 5,
            "Gd3+": 7,
            "Ho3+": 4,
            "La3+": 0.6,
            "Lu3+": 0.6,
            "Mn": 5,
            "Mn3+": 4,
            "Mn4+": 3,
            "Mo": 5,
            "Nd3+": 3,
            "Ni": 5,
            "Pm3+": 4,
            "Pr3+": 2,
            "Sm3+": 5,
            "Tb3+": 6,
            "Tm3+": 2,
            "V": 5,
            "W": 5,
            "Yb3+": 1,
        },
        LMAXMIX__smart_lmaxmix=True,
        multiple_keywords__smart_ldau=dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=1,
            LDAUJ={},  # pymatgen sets these, but they're all default values anyways
            LDAUL={
                "F": {
                    "Ag": 2,
                    "Co": 2,
                    "Cr": 2,
                    "Cu": 2,
                    "Fe": 2,
                    "Mn": 2,
                    "Mo": 2,
                    "Nb": 2,
                    "Ni": 2,
                    "Re": 2,
                    "Ta": 2,
                    "V": 2,
                    "W": 2,
                },
                "O": {
                    "Ag": 2,
                    "Co": 2,
                    "Cr": 2,
                    "Cu": 2,
                    "Fe": 2,
                    "Mn": 2,
                    "Mo": 2,
                    "Nb": 2,
                    "Ni": 2,
                    "Re": 2,
                    "Ta": 2,
                    "V": 2,
                    "W": 2,
                },
                "S": {
                    "Fe": 2,
                    "Mn": 2.5,
                },
            },
            LDAUU={
                "F": {
                    "Ag": 1.5,
                    "Co": 3.4,
                    "Cr": 3.5,
                    "Cu": 4,
                    "Fe": 4.0,
                    "Mn": 3.9,
                    "Mo": 4.38,
                    "Nb": 1.5,
                    "Ni": 6,
                    "Re": 2,
                    "Ta": 2,
                    "V": 3.1,
                    "W": 4.0,
                },
                "O": {
                    "Ag": 1.5,
                    "Co": 3.4,
                    "Cr": 3.5,
                    "Cu": 4,
                    "Fe": 4.0,
                    "Mn": 3.9,
                    "Mo": 4.38,
                    "Nb": 1.5,
                    "Ni": 6,
                    "Re": 2,
                    "Ta": 2,
                    "V": 3.1,
                    "W": 4.0,
                },
                "S": {
                    "Fe": 1.9,
                    "Mn": 2.5,
                },
            },
        ),
    )

    error_handlers = [
        TetrahedronMesh(),
        RotationMatrix(),
        Brmix(),
        Zpotrf(),
        SubspaceMatrix(),
        IncorrectShift(),
        RealOptlay(),
        Tetirr(),
        RotationNonIntMatrix(),
        LongVector(),
        TripleProduct(),
        Pricel(),
        Brions(),
        Zbrent(),
        InsufficientBands(),
        Pssyevx(),
        Eddrmm(),
        Edddav(),
        Edwav(),
        Zheev(),
        ElfKpar(),
        Rhosyg(),
        Posmap(),
        PointGroup(),
        SymprecNoise(),
        IncorrectSmearing(),
        MeshSymmetry(),
        Unconverged(),
        NonConverging(),
        Potim(),
        PositiveEnergy(),
        Frozen(),
        LargeSigma(),
        Walltime(),
    ]
