
# Single-Step VASP Relaxation

## About :star:

This script demonstrates how to run a single VASP relaxation using Simmate. We load a structure from a CIF file and run the `relaxation.vasp.matproj` workflow. This is a common "Hello World" task for using Simmate with external simulation codes.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] VASP installed and configured ([guide](/apps/vasp/installation.md))

## The script :rocket:

``` python
from simmate.toolkit import Structure
from simmate.workflows.utilities import get_workflow

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

# 2. Load the starting structure
structure = Structure.from_file("NaCl.cif")

# 3. Get the relaxation workflow
# We use the 'matproj' version which includes settings optimized for
# Materials Project-style calculations.
relax_workflow = get_workflow("relaxation.vasp.matproj")

# 4. Run the relaxation
# This will create a directory named 'simmate-task-XXXX' with the results.
state = relax_workflow.run(
    structure=structure,
    command="mpirun -n 4 vasp_std > vasp.out",
)

# 5. Access the results
if state.is_completed():
    print("VASP relaxation finished successfully!")
    
    # The final structure object is stored in the state result
    final_structure = state.result()
    print(f"Final Volume: {final_structure.volume:.2f} A^3")
else:
    print("VASP relaxation failed.")
```
