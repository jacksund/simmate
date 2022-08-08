# -*- coding: utf-8 -*-

from simmate.calculators.vasp.inputs import Poscar


def test_poscar(tmpdir, structure):
    filename = tmpdir / "POSCAR"
    Poscar.to_file(structure, filename)
    structure_new = Poscar.from_file(filename)
    assert structure == structure_new
