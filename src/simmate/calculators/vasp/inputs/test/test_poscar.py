# -*- coding: utf-8 -*-

from simmate.calculators.vasp.inputs import Poscar


def test_poscar(tmp_path, structure):
    filename = tmp_path / "POSCAR"
    Poscar.to_file(structure, filename)
    structure_new = Poscar.from_file(filename)
    assert structure == structure_new
