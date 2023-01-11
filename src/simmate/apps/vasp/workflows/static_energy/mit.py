# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit


class StaticEnergy__Vasp__Mit(Relaxation__Vasp__Mit):
    """
    Runs a VASP static energy calculation using MIT Project settings.

    This is identical to relaxation/mit, but just a single ionic step.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = Relaxation__Vasp__Mit.incar.copy()
    incar.update(
        dict(
            ALGO="Normal",
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
            KSPACING=0.4,  # was 0.5 # !!! This is where we are different from pymatgen right now
        )
    )
