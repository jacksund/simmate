
# Advanced NEB Path Finding

## About :star:

This script demonstrates how to define and run a custom Nudged Elastic Band (NEB) workflow. We chain together (i) bulk relaxation, (ii) path finding, (iii) supercell endpoint relaxations, and (iv) the final NEB image calculations.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Becca Radomsky                             |
| Github User     | [@becca9835](https://github.com/becca9835) |
| Last updated    | 2026.03.14                                 |
| Level           | **Advanced**                               |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] VASP installed and configured ([guide](/apps/vasp/installation.md))
- [x] [VTST-tools](https://theory.cm.utexas.edu/vtsttools/neb.html) (for CI-NEB support)

## The script :rocket:

``` python
from simmate.toolkit import Structure
from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow
from simmate.apps.vasp.workflows.diffusion import (
    NebAllPathsWorkflow,
    SinglePathWorkflow,
    VaspNebFromImagesWorkflow,
)

# 1. Create a sample structure for this example
# We'll use LiFePO4 as a classic diffusion example.
structure = Structure.from_dynamic("LiFePO4")

# 2. Define custom VASP settings for each stage of the NEB analysis
# We inherit from VaspWorkflow to set our preferred INCAR tags.

class BulkRelaxation(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(EDIFF=1e-06, ENCUT=520, ISIF=3, NSW=99, KSPACING=0.4)

class EndpointRelaxation(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(EDIFF=5e-05, EDIFFG=-0.02, ENCUT=520, ISIF=2, NSW=99, KSPACING=0.5)

class CI_NEB_Images(VaspNebFromImagesWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS
    _incar = dict(
        EDIFF=5e-05, EDIFFG=-0.05, ENCUT=520, NSW=99, KSPACING=0.5,
        LCLIMB=True, SPRING=-5, IOPT=1, # CI-NEB settings
    )

# 3. Piece the workflows together into a single "All Paths" workflow

class MySinglePath(SinglePathWorkflow):
    endpoint_relaxation_workflow = EndpointRelaxation
    from_images_workflow = CI_NEB_Images

class MyAllPathsNEB(NebAllPathsWorkflow):
    bulk_relaxation_workflow = BulkRelaxation
    single_path_workflow = MySinglePath

# 4. Run the full analysis
# This will find all unique diffusion paths for Li and run NEB on each.
result = MyAllPathsNEB.run(
    structure=structure,
    migrating_specie="Li",
    command="mpirun -n 12 vasp_std > vasp.out",
    relax_bulk=True,
    relax_endpoints=True,
    nimages=5,
    min_supercell_atoms=80,
    max_supercell_atoms=240,
    min_supercell_vector_lengths=10,
    max_path_length=5,
)
```
