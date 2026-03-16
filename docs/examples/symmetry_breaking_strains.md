
# Symmetry-Breaking Strains

## About :star:

This script demonstrates how to use the Simmate `toolkit` to manipulate crystal structures and analyze their symmetry. We load a base structure, apply a randomized lattice strain to "break" its symmetry, and then use symmetry analysis to see how the spacegroup has changed. This is a common workflow for generating starting structures for high-throughput relaxation studies or evolutionary searches.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

*No extra configuration is required for this script.*

## The script :rocket:

``` python
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from simmate.toolkit import Structure
from simmate.toolkit.transformations import LatticeStrain

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

# 2. Load the structure
structure = Structure.from_file("NaCl.cif")

# 3. Analyze the initial symmetry
# We use pymatgen's SpacegroupAnalyzer for this.
vga_orig = SpacegroupAnalyzer(structure)
print(f"Original Spacegroup: {vga_orig.get_space_group_symbol()} ({vga_orig.get_space_group_number()})")

# 4. Apply a Lattice Strain transformation
# This transformation randomly shifts lattice vectors while maintaining volume.
# It is useful for 'shaking' a structure to explore nearby local minima.
transformer = LatticeStrain()
strained_structure = transformer.apply_transformation(
    structure=structure,
    fixed_volume=structure.volume,
)

# 5. Analyze the new symmetry
vga_new = SpacegroupAnalyzer(strained_structure)
print(f"Strained Spacegroup: {vga_new.get_space_group_symbol()} ({vga_new.get_space_group_number()})")

# 6. Detect if the transformation actually broke symmetry
if vga_orig.get_space_group_number() != vga_new.get_space_group_number():
    print("Success! Symmetry was broken by the transformation.")
else:
    print("The transformation was too small to change the detected spacegroup.")
```
