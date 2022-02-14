# -*- coding: utf-8 -*-

import os

from simmate.calculators.vasp.inputs import Poscar


def test_poscar(tmpdir, structure):
    filename = os.path.join(tmpdir, "POSCAR")
    Poscar.to_file(structure, filename)
    structure_new = Poscar.from_file(filename)
    assert structure == structure_new
