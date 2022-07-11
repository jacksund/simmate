# -*- coding: utf-8 -*-

from pymatgen.core import Species

from simmate.toolkit import Structure
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.tasks.static_energy import MatprojStaticEnergy


class MatprojNMRElectricFieldGradiant(MatprojStaticEnergy):
    """
    This task is a reimplementation of pymatgen's
    [MPNMRSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="efg" (Electric Field Gradient).
    """

    incar = MatprojStaticEnergy.incar.copy()
    incar.update(
        dict(
            ALGO="FAST",
            EDIFF=-1.0e-10,
            ISYM=0,
            LCHARG=False,
            LEFG=True,
            QUAD_EFG__smart_quad_efg=True,
            NELMIN=10,
            PREC="ACCURATE",
            SIGMA=0.01,
        )
    )
    incar.pop("EDIFF__per_atom")


def keyword_modifier_smart_quad_efg(structure: Structure, quad_efg_config):
    """
    When running NMR (nuclear magnetic resonance) calculations that evaluate
    the electric field gradient, we need to set quadrapole moments for
    each species in our structure.

    NOTE: this modifier may be converted to a workflow parameter in the
    future.
    """
    # This code is copy/pasted from pymatgen (with minor edits)
    # See..
    # https://github.com/materialsproject/pymatgen/blob/1b6d1d2212dcf3a559cb2c489dd25e9754f9f788/pymatgen/io/vasp/sets.py#L1940-L1942

    # TODO: maybe use quad_efg_config to set this for different isotopes.
    # For now, I just use the VASP default
    isotopes = []

    isotopes = {ist.split("-")[0]: ist for ist in isotopes}
    quad_efg = [
        Species(element.symbol).get_nmr_quadrupole_moment(
            isotopes.get(element.symbol, None)
        )
        for element in structure.composition.elements
    ]

    # there is a unit (mbarn) attached to each so we clear these
    quad_efg = [float(q) for q in quad_efg]

    return quad_efg


Incar.add_keyword_modifier(keyword_modifier_smart_quad_efg)
