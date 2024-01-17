# -*- coding: utf-8 -*-

from simmate.apps.vasp.error_handlers import (  # Frozen,
    Brions,
    Brmix,
    Edddav,
    Eddrmm,
    Edwav,
    ElfKpar,
    IncorrectShift,
    IncorrectSmearing,
    InsufficientBands,
    LargeSigma,
    LongVector,
    MeshSymmetry,
    NonConverging,
    PointGroup,
    PositiveEnergy,
    Posmap,
    Potim,
    Pricel,
    Pssyevx,
    RealOptlay,
    Rhosyg,
    RotationMatrix,
    RotationNonIntMatrix,
    SubspaceMatrix,
    SymprecNoise,
    Tetirr,
    TetrahedronMesh,
    TripleProduct,
    Unconverged,
    Walltime,
    Zbrent,
    Zheev,
    Zpotrf,
)
from simmate.apps.vasp.inputs.potcar_mappings import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__WarrenLabPbe(VaspWorkflow):
    """
    Runs a VASP geometry optimization using preferred settings from the Warren lab.

    """

    description_doc_short = "Warren Lab's presets for PBE optimization"

    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    # For now I'm keeping the matproj default element mappings, but I will likely
    # update these for future calculations.

    _incar = dict(
        ALGO="Fast",
        EDIFF__per_atom=5e-05,  # This is slightly higher quality than the settings in Simmate (5e-05)
        ENCUT=520,  # Should set dynamically in future
        IBRION=2,
        ISIF=3,
        ISMEAR=0,  # Gaussian smearing
        ISPIN=2,
        KSPACING=0.25,  # This is probably on the edge of good quality
        LASPH=True,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=150,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
        IVDW=12,  # adds van der waals correction
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
        #        Frozen(),
        LargeSigma(),
        Walltime(),
    ]
