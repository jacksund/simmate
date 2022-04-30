# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import MITRelaxation


class MatVirtualLabCINEBEndpointRelaxation(MITRelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MVLCINEBEndPointSet](http://guide.materialsvirtuallab.org/pymatgen-analysis-diffusion/pymatgen.analysis.diffusion.neb.io.html#pymatgen.analysis.diffusion.neb.io.MVLCINEBEndPointSet).

    Runs a VASP relaxation calculation using MIT Project settings, where some
    settings are adjusted to accomodate large supercells with defects. Most
    notably, the lattice remains fixed and symmetry is turned off for this
    relaxation.

    These settings are closely related to relaxation/mit, but only meant to be
    used on start/end supercell structures of a NEB calculation.

    You typically shouldn't use this workflow directly, but instead use the
    higher-level NEB workflows (e.g. diffusion/neb_all_paths or
    diffusion/neb_from_endpoints), which call this workflow for you.
    """

    incar = MITRelaxation.incar.copy()
    incar.update(
        dict(
            EDIFF=5e-5,
            ISIF=2,  # hold lattice volume and shape constant
            EDIFFG=-0.02,
            ISMEAR=0,
            ISYM=0,
            LCHARG=False,
            # LDAU=False,
            NELMIN=4,
        )
    )
    incar.pop("multiple_keywords__smart_ldau")
