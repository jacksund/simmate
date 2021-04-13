This module is empty at the moment, but I plan for it to be a fork/merge of pymatgen.core and ase in the future. For now, I just use these packages as dependencies directly. I call this 'materials_science' instead of 'core' or 'engine' to help beginner users, but I may change this back in the future.


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

