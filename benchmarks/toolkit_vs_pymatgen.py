# -*- coding: utf-8 -*-

from simmate.toolkit.lattice import Lattice
lattice = Lattice(matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
%time lattice.lengths
%timeit lattice.lengths
%timeit lattice.b

from pymatgen.core.lattice import Lattice
lattice = Lattice(matrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
%time lattice.lengths
%timeit lattice.lengths
%timeit lattice.b
