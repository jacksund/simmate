VASP Workflow Library
--------------------

This module defines settings for common VASP workflows.

Many workflows can be considered a fork and refactor of classes used by [PyMatGen](https://github.com/materialsproject/pymatgen/) and [Atomate](https://github.com/hackingmaterials/atomate). Specifically, this is a direct alternative to the [`pymatgen.io.vasp.sets`](https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/vasp/sets.py) module as well as the [`atomate.vasp.workflows`](https://github.com/hackingmaterials/atomate/tree/main/atomate/vasp/workflows) module. Rather than build these tasks from many lower-level functions, we condense these classes down into a single `VaspWorkflow` class that is easier to interact with.
