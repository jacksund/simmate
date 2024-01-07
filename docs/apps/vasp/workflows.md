VASP Workflow Library
--------------------

This module outlines the configurations for standard VASP workflows.

Numerous workflows are essentially a division and restructuring of classes utilized by [PyMatGen](https://github.com/materialsproject/pymatgen/) and [Atomate](https://github.com/hackingmaterials/atomate). Specifically, this serves as a direct substitute to the [`pymatgen.io.vasp.sets`](https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/vasp/sets.py) module and the [`atomate.vasp.workflows`](https://github.com/hackingmaterials/atomate/tree/main/atomate/vasp/workflows) module. Instead of constructing these tasks from numerous lower-level functions, we simplify these classes into a single `VaspWorkflow` class for easier interaction.