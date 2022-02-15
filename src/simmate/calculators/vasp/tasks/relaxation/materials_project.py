# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS,
)
from simmate.calculators.vasp.error_handlers import (
    TetrahedronMesh,
    Eddrmm,
    IncorrectSmearingHandler,
    MeshSymmetryErrorHandler,
    UnconvergedErrorHandler,
    NonConvergingErrorHandler,
    PotimErrorHandler,
    PositiveEnergyErrorHandler,
    FrozenErrorHandler,
    LargeSigmaErrorHandler,
)


class MatProjRelaxation(VaspTask):
    """
    Runs a VASP geometry optimization using Materials Project settings.

    This is currently the highest-quality preset of all of Simmate's relaxations.

    Materials Project settings are often considered the minimum-required
    quality for publication and is sufficient for most applications. If you are
    looking at one structure in detail (for electronic, vibrational, and other
    properties), you should still test for convergence using higher-quality
    settings.
    """

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria.
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS

    # These are all input settings for this task. Note a lot of settings
    # depend on the structure/composition being analyzed.
    incar = dict(
        # These settings are the same for all structures regardless of composition
        ALGO="Fast",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        IBRION=2,
        ISIF=3,
        ISMEAR=-5,
        ISPIN=2,
        ISYM=0,
        KSPACING=0.4,  # !!! This is where we are different from pymatgen right now
        LASPH=True,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=100,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
        # The magnetic moments are dependent on what the composition and oxidation
        # states are. Note our default of 0.6 is different from the VASP default too.
        MAGMOM__smart_magmom={
            "default": 0.6,
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
        # We run LDA+U for certain compositions. This is a complex configuration
        # so be sure to read the "__smart_ldau" modifier for more information.
        # But as an example for how the mappings work...
        # {"F": {"Ag": 2}} means if the structure is a fluoride, then we set
        # the MAGMOM for Ag to 2. Any element that isn't listed defaults to 0.
        multiple_keywords__smart_ldau=dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=1,
            LMAXMIX__auto=True,
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

    # These are some default error handlers to use
    error_handlers = [
        TetrahedronMesh(),
        Eddrmm(),
        IncorrectSmearingHandler(),
        MeshSymmetryErrorHandler(),
        UnconvergedErrorHandler(),
        NonConvergingErrorHandler(),
        PotimErrorHandler(),
        PositiveEnergyErrorHandler(),
        FrozenErrorHandler(),
        LargeSigmaErrorHandler(),
    ]
