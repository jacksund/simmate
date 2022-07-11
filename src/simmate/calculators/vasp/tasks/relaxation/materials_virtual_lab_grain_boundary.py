# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import MatprojRelaxation


class MatVirtualLabGrainBoundaryRelaxation(MatprojRelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MVLGBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLGBSet).
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = MatprojRelaxation.incar.copy()
    incar.update(
        dict(
            LCHARG=False,
            NELM=60,
            PREC="Normal",
            EDIFFG=-0.02,
            ICHARG=0,
            NSW=200,
            EDIFF=0.0001,
            # pymatgen has user set is_metal, where default is True and there
            # is no advanced logic. We just assume metal for now.
            ISMEAR=1,
            LDAU=False,
            KSPACING=0.35,  # !!! this is approximate to pymatgen
        )
    )
    incar.pop("multiple_keywords__smart_ldau")
    incar.pop("EDIFF__per_atom")
