# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.badelf.prebadelf_dft import (
    StaticEnergy__Vasp__WarrenLabPrebadelfPbesol,
)
from simmate.apps.warren_lab.workflows.nested_dft.relaxation_static_base import (
    RelaxationStaticBase,
)
from simmate.apps.warren_lab.workflows.relaxation.pbesol import (
    Relaxation__Vasp__WarrenLabPbesol,
)


class Nested__Vasp__WarrenLabRelaxationStaticPbePbe(RelaxationStaticBase):
    """
    Runs an PBEsol quality structure relaxation and PBEsol quality static energy
    calculation.This method will also write the ELFCARand CHGCAR files necessary
    for population analysis (i.e. oxidation state and electron count)
    """

    static_energy_workflow = StaticEnergy__Vasp__WarrenLabPrebadelfPbesol
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
    relaxation_workflow = Relaxation__Vasp__WarrenLabPbesol
