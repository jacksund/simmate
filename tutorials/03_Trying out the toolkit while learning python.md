# Trying out the toolkit while learning python

## The quick version

1. In python console (bottom right) run `import simmate` to make sure everything is set up.
2. Make sure you still have our `POSCAR` file of Silver (Ag) from the last tutorial. 
3. Now let's explore the toolkit and a few of its features!

Load the structure into python and then write it to a CIF file
```python
from simmate.shortcuts import Structure
structure = Structure.from_file("POSCAR")
structure.to("cif", "Ag.cif")
```

Grab varius properties of the structure
```python
# explore structure-based properties
structure.density
structure.distance_matrix
structure.coordinates_cartesian
structure.nsites

# grab the structure's composition and access it's properties
compositon = structure.composition
composition.formula_reduced
composition.elements

# grab the structure's lattice and access it's properties
lattice = structure.lattice
lattice.volume
lattice.matrix
lattice.angle_beta
```

Make new structures using some tranformation or analysis
```python
# all get_* methods leave the original structure unchanged and return a new structure
new_structure_01 = structure.get_supercell([2,2,2])
new_structure_02 = structure.get_conventional_unitcell()
new_structure_03 = structure.get_primitive_unitcell()
new_structure_04 = structure.get_oxidation_states()
```

What about advanced features?
```python
# Generate a RDF fingerprint to help analyze and compare structures
from simmate.toolkit.fingerprints.all import RdfFingerprint
fingerprint_analyzer = RdfFingerprint()
rdf = fingerprint_analyzer.get_fingerprint(structure)

# Create a random structure from a spacegroup and composition
from simmate.toolkit.creators.all import PyXtalCreator
creator = PyXtalCreator(composition)
structure = creator.new_structure(spacegroup=166)

# Check if two structures are matching
from simmate.toolkit.matching import StructureMatcher
matcher = StructureMatcher
is_matching = matcher.match(structure1, structure2)
```
There are many more features available! If you can't find what you're looking for, be sure to ask for help before trying to code something on your own. Chances are that the feature exists somewhere -- and if we don't have it, we'll direct you to a package that does.

## The full tutorial

This tutorial will include...
- python console vs. the regular console (terminal/command prompt)
- Analogy of txt with Word/Google Docs --> python with Spyder
- Intro to Spyder and its components
- the basics of Structure data
- writing a function for lattice volume
- the Structure object and its many methods
- loading from & writing to a file
