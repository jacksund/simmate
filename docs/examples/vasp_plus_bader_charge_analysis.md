
# VASP + Bader Charge Analysis

## About :star:

This script demonstrates how to chain multiple simulation apps together. We first run a VASP relaxation and then automatically follow it with a Bader population analysis. Simmate handles the complex file-shuffling (passing `CHGCAR`, `AECCAR0`, etc.) between the two codes.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Intermediate**                           |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] VASP installed and configured ([guide](/apps/vasp/installation.md))
- [x] [Bader executable](http://theory.cm.utexas.edu/henkelman/code/bader/) in your PATH

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

# 3. Run the VASP relaxation
relax_workflow = get_workflow("relaxation.vasp.matproj")
relax_state = relax_workflow.run(
    structure=structure,
    command="mpirun -n 4 vasp_std > vasp.out",
)

# 4. Check if VASP finished, then start Bader analysis
if relax_state.is_completed():
    print("VASP relaxation finished! Starting Bader analysis...")
    
    # 5. Get the Bader workflow
    bader_workflow = get_workflow("population-analysis.vasp-bader.bader-matproj")
    
    # 6. Run Bader analysis using the results from the relaxation
    # We pass the directory of the previous run so Simmate can find
    # the CHGCAR and AECCAR files.
    bader_state = bader_workflow.run(
        copy_previous_directory=relax_state.directory,
    )
    
    if bader_state.is_completed():
        print("Bader analysis complete!")
    else:
        print("Bader analysis failed.")
else:
    print("VASP relaxation failed. Skipping Bader analysis.")
```
