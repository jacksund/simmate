from simmate.apps.warren_lab.workflows.baderkit.base import BaderkitStagedBase
from simmate.apps.baderkit.workflows import Baderkit__Baderkit__ElfRadii, Baderkit__Baderkit__Bader
from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import StaticEnergy__Vasp__PreRadiiWarren


class Baderkit__VaspBaderkit__RadiiPbesolWarren(BaderkitStagedBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """
    
    workflows = [
        StaticEnergy__Vasp__PreRadiiWarren,
        Baderkit__Baderkit__Bader,
        Baderkit__Baderkit__ElfRadii
        ]
