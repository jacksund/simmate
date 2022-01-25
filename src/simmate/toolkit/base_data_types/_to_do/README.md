
> :warning: This module is entirely experimental and should not be used at the moment. Instead, users should use the `pymatgen.core` module.

This is intended to be a fork and refactor of the `pymatgen.core` module. We are still at the outlining stage for it.

## notes on types on classes

element (string + mapped data)
lattice (3x3 matrix)

specie/ion (element+charge/oxidation_state)
    + dummyspecie
site (element+coords)

periodic site (site+lattice)

molecule (many sites)
structure (many periodic sites)

molecular crystal (many molecules + coords + lattice)

compositon (many elements)


transformations
buidlers (or generators)

symmetry (via spglib)
    symmetry_analyzer
    operation
    symmstructure


Others...
    molecular orbital
    bond
    spectrum
    neighbor (reduced version of site class for speed)
    slab/surface (+ its generator)
    Tensor (TensorCollection, SquareTensor, TensorMapping)
    Trajectory (for MD)
    iStructure, iMolecule, SiteCollection
    Units (float + string + mappings)
    XvFunc (XC correlation functional)

