# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Relaxation__Vasp__MatprojPbesol(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPRelaxSet).

    Runs a VASP geometry optimization using Materials Project settings with
    added settings for PBEsol.

    Materials Project settings are often considered the minimum-required
    quality for publication and is sufficient for most applications. If you are
    looking at one structure in detail (for electronic, vibrational, and other
    properties), you should still test for convergence using higher-quality
    settings.
    """

    description_doc_short = "based on pymatgen's MPMetalRelaxSet"

    # Tell VASP to use PBEsol instead of base PBE
    _incar_updates = dict(GGA="PS")
