# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.mit import MITRelaxation


class NEBEndpointRelaxation(MITRelaxation):
    """
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

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # These settings are based off of pymatgen's MVLCINEBEndPointSet
    # http://guide.materialsvirtuallab.org/pymatgen-analysis-diffusion/pymatgen.analysis.diffusion.neb.io.html
    incar = MITRelaxation.incar.copy()
    incar.update(
        dict(
            ISIF=2,  # hold lattice volume and shape constant
            EDIFFG=-0.02,
            ISMEAR=0,
            ISYM=0,
            LDAU=False,
            NELMIN=4,
        )
    )
    # We set ISMEAR=0 and SIGMA above, so we no longer need smart_ismear
    incar.pop("multiple_keywords__smart_ismear")
    # LDA+U is turned off
    incar.pop("multiple_keywords__smart_ldau")
