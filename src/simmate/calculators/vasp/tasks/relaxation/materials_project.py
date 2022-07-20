# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS,
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


class MatprojRelaxation(VaspTask):
    """
    This task is a reimplementation of pymatgen's
    [MPRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPRelaxSet).

    Runs a VASP geometry optimization using Materials Project settings.

    Materials Project settings are often considered the minimum-required
    quality for publication and is sufficient for most applications. If you are
    looking at one structure in detail (for electronic, vibrational, and other
    properties), you should still test for convergence using higher-quality
    settings.
    """

    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS

    incar = dict(
        ALGO="Fast",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        IBRION=2,
        ISIF=3,
        ISMEAR=-5,
        ISPIN=2,
        KSPACING=0.4,  # !!! This is where we are different from pymatgen right now
        LASPH=True,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=100,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
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
                    "Co": 2,
                    "Cr": 2,
                    "Fe": 2,
                    "Mn": 2,
                    "Mo": 2,
                    "Ni": 2,
                    "V": 2,
                    "W": 2,
                },
                "O": {
                    "Co": 2,
                    "Cr": 2,
                    "Fe": 2,
                    "Mn": 2,
                    "Mo": 2,
                    "Ni": 2,
                    "V": 2,
                    "W": 2,
                },
            },
            LDAUU={
                "F": {
                    "Co": 3.32,
                    "Cr": 3.7,
                    "Fe": 5.3,
                    "Mn": 3.9,
                    "Mo": 4.38,
                    "Ni": 6.2,
                    "V": 3.25,
                    "W": 6.2,
                },
                "O": {
                    "Co": 3.32,
                    "Cr": 3.7,
                    "Fe": 5.3,
                    "Mn": 3.9,
                    "Mo": 4.38,
                    "Ni": 6.2,
                    "V": 3.25,
                    "W": 6.2,
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
