# Simmate Toolkit Overview

!!! danger
    Please note that many classes within this module are still under development. We recommend using [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase) for toolkit functionality until Simmate reaches v1.0.0. For developers, this implies that numerous classes are currently undocumented and untested. This approach enables us to expedite our testing process without the need to reformat tests and rewrite guides. We include this developmental code in our main branch because some higher-level functions (e.g., workflows) depend on these features. However, we ensure that these higher-level functions are thoroughly tested and documented to counterbalance the ongoing changes at the lower level.

The toolkit module aims to extend [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase). It encompasses low-level classes and functions, such as the `Structure` class and its associated methods. The toolkit module is entirely Python-based and does not rely on third-party DFT programs. For those, please refer to the `simmate.apps` module.

The `Structure` and `Composition` classes are the most frequently used classes from this toolkit. You can import these classes using the following code:

``` python
from simmate.toolkit import Structure, Composition
```

## Submodules Overview

- `base_data_types`: Defines core classes for materials science, including `Structure` and `Composition` classes. For ease of use, these classes can be directly imported from `simmate.toolkit`, as shown above.
- `creators`: Aids in the creation of structures, lattices, and periodic sites.
- `featurizers`: Transforms properties into numerical descriptors for machine learning applications.
- `structure_prediction`: Predicts crystal structures using an evolutionary algorithm.
- `symmetry`: Provides tools and metadata for symmetry analyses, such as space groups and Wyckoff sites.
- `transformations`: Offers methods to transform or "mutate" `Structures`.
- `validators`: Provides methods to verify if a structure meets specific criteria.