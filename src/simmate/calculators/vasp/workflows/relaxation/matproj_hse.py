# -*- coding: utf-8 -*-

from simmate.calculators.vasp.error_handlers import (
    Brions,
    Brmix,
    Edddav,
    Eddrmm,
    Edwav,
    ElfKpar,
    Frozen,
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
from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__MatprojHse(VaspWorkflow):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet).

    Runs a VASP relaxation calculation using Materials Project HSE settings.
    """

    description_doc_short = "based on pymatgen's MPHSERelaxSet"

    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS

    incar = dict(
        ALGO="All",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        HFSCREEN=0.2,
        IBRION=2,
        ICHARG=1,
        ISIF=3,
        ISMEAR=0,
        ISPIN=2,
        LHFCALC=True,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=100,
        NSW=99,
        PREC="Accurate",
        PRECFOCK="Fast",
        SIGMA=0.05,
        KSPACING=0.4,  # !!! This is where we are different from pymatgen right now
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
