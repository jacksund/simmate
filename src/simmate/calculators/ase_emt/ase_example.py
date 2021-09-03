# -*- coding: utf-8 -*-

# Grab a small pre-optimized structure to do quick calcs with
from pymatgen import MPRester

mpr = MPRester("2Tg7uUvaTAPHJQXl")
structure = mpr.get_structure_by_material_id("mp-23")  # 23 # 976762

# I loaded an already-optimizated structure, so I need to strain the lattice
# a randomly rattle the sites a bit. This tests out the geometry optimization.
structure.scale_lattice(structure.volume * 0.6)  # distort lattice away from global min
structure.perturb(0.1)

# convert to ASE atoms object
from pymatgen.io.ase import AseAtomsAdaptor

structure_ase = AseAtomsAdaptor.get_atoms(structure)

# attach the EMT calculator
from ase.calculators.emt import EMT

structure_ase.calc = EMT()

# I wrap the ase atoms in a filter so that the lattice is also optimized
# Still don't understand why they make this such a confusing extra step...
# https://wiki.fysik.dtu.dk/ase/ase/constraints.html#ase.constraints.ExpCellFilter
from ase.constraints import ExpCellFilter

ecf = ExpCellFilter(structure_ase)

# optimize the structure
# see https://wiki.fysik.dtu.dk/ase/ase/optimize.html#module-ase.optimize.basin
# and benchmarks https://wiki.fysik.dtu.dk/gpaw/devel/ase_optimize/ase_optimize.html
from ase.optimize import GPMin

opt = GPMin(ecf)  # If only optimizing sites, just pass structure_ase atoms object
opt.run(fmax=1e-2, steps=50)

# grab the optimized structure
structure_ase = (
    opt.atoms.atoms
)  # just one .atoms if I passed structure_ase above instead of filter

# calculate the energy per atom for the final structure
#!!! Is there an easy way to grab this from the opt ouptut object?
energy = structure_ase.get_potential_energy() / len(structure_ase)

# convert back to pymatgen structure
structure_opt = AseAtomsAdaptor.get_structure(structure_ase)
