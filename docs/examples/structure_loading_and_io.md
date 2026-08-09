
# Structure Loading & I/O

## About :star:

This script demonstrates the most basic interactions with crystal structures in Simmate. We show how to load a structure from a file (like a CIF or POSCAR), access its fundamental properties (volume, density, etc.), and export it to a different format.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

*No extra configuration is required for this script.*

## The script :rocket:

``` python
from simmate.toolkit import Structure

# 1. Create a sample CIF file for this example
# Normally you would already have a 'NaCl.cif' file.
cif_content = """
data_NaCl
_cell_length_a 5.64
_cell_length_b 5.64
_cell_length_c 5.64
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'F m -3 m'
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Na 0.00000 0.00000 0.00000
Cl 0.50000 0.50000 0.50000
"""
with open("NaCl.cif", "w") as f:
    f.write(cif_content)

# 2. Load a structure from a file
# Simmate automatically detects the format (CIF, POSCAR, etc.)
structure = Structure.from_file("NaCl.cif")

# 3. Access basic properties
# These are inherited from PyMatGen, so all standard methods work!
print(f"Formula: {structure.composition.reduced_formula}")
print(f"Volume: {structure.volume:.2f} A^3")
print(f"Density: {structure.density:.2f} g/cm^3")
print(f"Number of sites: {structure.num_sites}")

# 4. Modify the structure (e.g. make a supercell)
structure.make_supercell([2, 2, 2])
print(f"New number of sites: {structure.num_sites}")

# 5. Export to a different format
# We can export to a variety of formats including 'poscar', 'cif', 'json', etc.
structure.to(filename="NaCl_supercell.vasp", fmt="poscar")
print("Exported NaCl_supercell.vasp")

# 6. Accessing lattice and sites
print(f"Lattice angles: {structure.lattice.angles}")
for site in structure.sites[:3]: # limit output for readability
    print(f"Element: {site.specie.symbol}, Coordinates: {site.coords}")
```
