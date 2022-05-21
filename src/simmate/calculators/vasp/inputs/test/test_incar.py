# -*- coding: utf-8 -*-

import os

from simmate.calculators.vasp.inputs import Incar


def test_incar(tmpdir, structure):

    # TODO: make a fixture of INCAR settings to iterate through.

    # These settings are taken from the relaxation/quality00 task
    settings1 = dict(
        PREC="Low",
        EDIFF=2e-3,
        EDIFFG=-2e-1,
        ISIF=4,
        NSW=75,
        IBRION=2,
        POTIM=0.02,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.75,
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=1,
                SIGMA=0.1,
            ),
            "non-metal": dict(
                ISMEAR=0,
                SIGMA=0.05,
            ),
        },
    )

    # These settings are taken from the relaxation/mat-proj task
    settings2 = dict(
        ALGO="Fast",
        EDIFF__per_atom=5.0e-05,
        ENCUT=520,
        IBRION=2,
        ISIF=3,
        ISMEAR=-5,
        ISPIN=2,
        ISYM=0,
        KSPACING=0.4,
        LASPH=True,
        LORBIT=11,
        LREAL="Auto",
        LWAVE=False,
        NELM=100,
        NSW=99,
        PREC="Accurate",
        SIGMA=0.05,
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
        multiple_keywords__smart_ldau=dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=1,
            LDAUJ={},
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

    # These settings are taken from the relaxation/mit task
    settings3 = dict(
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
        KSPACING=0.5,
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
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=2,
                SIGMA=0.2,
            ),
            "non-metal": dict(
                ISMEAR=-5,
                SIGMA=0.05,
            ),
        },
        multiple_keywords__smart_ldau=dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=1,
            LDAUJ={},
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

    incar1 = Incar(**settings1)
    incar1.to_file(
        filename=os.path.join(tmpdir, "INCAR"),
        structure=structure,
    )

    incar2 = Incar(**settings2)
    incar2.to_file(
        filename=os.path.join(tmpdir, "INCAR"),
        structure=structure,
    )

    incar3 = Incar(**settings3)
    incar3.to_file(
        filename=os.path.join(tmpdir, "INCAR"),
        structure=structure,
    )

    # simply check that we can reload. Checking for values and logic should be
    # done with individual keyword modifiers
    incar4 = Incar.from_file(os.path.join(tmpdir, "INCAR"))

    # TODO: assert equal to ....
    diff = incar1.compare_incars(incar2)


def test_custom_keyword_modifier(tmpdir, sample_structures):

    structure = sample_structures["C_mp-48_primitive"]

    incar_filename = os.path.join(tmpdir, "INCAR")

    # make a dummy modifier that just multiplies input by 2
    def keyword_modifier_dummy(structure, value):
        return value * 2

    Incar.add_keyword_modifier(keyword_modifier_dummy)

    # simple tests to confirm method is registered
    assert hasattr(Incar, "keyword_modifier_dummy")
    assert Incar.keyword_modifier_dummy(None, 4) == 8

    # now test out logic with keyword
    incar = Incar(ENCUT__dummy=4)
    incar.to_file(
        filename=incar_filename,
        structure=structure,
    )

    incar2 = Incar.from_file(incar_filename)
    assert incar2.get("ENCUT", None) == 8
