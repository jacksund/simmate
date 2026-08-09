
# Molecule Filtering

## About :star:

This script demonstrates how to use Simmate's `Molecule` toolkit to load a set of molecules and filter them based on specific chemical properties, such as the number of stereocenters, heavy atoms, and elemental composition.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

*No extra configuration is required for this script.*

## The script :rocket:

``` python
from simmate.toolkit import Molecule

# 1. Create a sample SDF file for this example
# Normally you would already have an 'example.sdf' file.
sdf_content = """
Molecule 1
  Simmate
            3D
 12 12  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.2500    1.2990    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    2.5981    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    2.5981    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7500    1.2990    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    0.0000    1.5000 O   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    0.0000    1.5000 O   0  0  0  0  0  0  0  0  0  0  0  0
    2.2500    1.2990    1.5000 N   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    2.5981    1.5000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    2.5981    1.5000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.7500    1.2990    1.5000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0
  2  3  1  0
  3  4  1  0
  4  5  1  0
  5  6  1  0
  6  1  1  0
  7  8  1  0
  8  9  1  0
  9 10  1  0
 10 11  1  0
 11 12  1  0
 12  7  1  0
M  END
$$$$
"""
with open("example.sdf", "w") as f:
    f.write(sdf_content)

# 2. Load molecules from the SDF file
molecules = Molecule.from_sdf_file("example.sdf")

# 3. Filter molecules based on specific criteria
molecules_filtered = []
for molecule in molecules:
    # Skip if it has more than 3 stereocenters
    if molecule.num_stereocenters > 3:
        continue
    
    # Skip if it has more than 30 heavy atoms
    if molecule.num_atoms_heavy > 30:
        continue
    
    # Skip if it contains Sodium (Na)
    if "Na" in molecule.elements:
        continue
    
    molecules_filtered.append(molecule)

# 4. Export the filtered results (e.g., to InChI keys)
inchi_keys = [m.to_inchi_key() for m in molecules_filtered]

print(f"Filtered {len(molecules)} molecules down to {len(molecules_filtered)}.")
print(f"First InChI Key: {inchi_keys[0]}")
```
