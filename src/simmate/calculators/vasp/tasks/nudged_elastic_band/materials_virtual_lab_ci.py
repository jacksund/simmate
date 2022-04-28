# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.nudged_elastic_band.mit import MITNudgedElasticBand


class MatVirtualLabCINEB(MITNudgedElasticBand):
    """
    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.

    You shouldn't use this workflow directly, but instead use the higher-level
    NEB workflows (e.g. diffusion/neb_all_paths or diffusion/neb_from_endpoints),
    which call this workflow for you.

    Note that these parameters require the VTST modification of VASP from the
    Henkelman group. See http://theory.cm.utexas.edu/vtsttools/
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = MITNudgedElasticBand.incar.copy()
    incar.update(
        dict(
            EDIFFG=-0.02,
            IBRION=3,
            ICHAIN=0,
            IOPT=1,
            ISIF=2,
            ISMEAR=0,
            LCLIMB=True,
            LORBIT=0,
            NSW=200,
            POTIM=0,
            SPRING=-5,
        )
    )
