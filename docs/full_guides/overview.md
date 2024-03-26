# Full Guides

!!! note
    Before using the full guides, ensure you have either completed our [introductory tutorials](/simmate/getting_started/overview/) or have a good understanding of Python.

## Organization Overview

The structure of our guides and code may not always match. We've found that separating the two helps newcomers navigate Simmate without having to grasp all its components at once.

### Documentation

Our guides are arranged in order to mirror the typical user journey with Simmate. Users generally start with high-level features (the website interface) and progressively delve into lower-level features (the toolkit and Python objects). The documentation mirrors this progression.

``` mermaid
graph LR
  A[Website] --> B[Workflows];
  B --> C[Database];
  C --> D[Toolkit];
  D --> E[Extras];
```

### Source Code

For our python modules, `simmate` is the base module, housing all the code that our package operates on. Each subfolder (or Python "module") provides detailed information about its contents.

These modules include:

- `apps`: Runs specific analyses or third-party programs (e.g., VASP, which performs DFT calculations)
- `command_line`: Provides common functions as terminal commands
- `configuration`: Contains default Simmate settings and methods for modifying them
- `database`: Sets up data table structures and methods for accessing these tables
- `engine`: Offers tools for running calculations and managing errors
- `file_converters`: Includes methods for converting between file types (e.g., POSCAR to CIF)
- `toolkit`: Houses core methods and classes for Simmate (e.g., the `Structure` class)
- `utilities`: Contains simple functions used across other modules
- `visualization`: Provides methods for visualizing structures and data
- `website`: Powers the simmate.org website
- `workflows`: Contains tools defining each calculation type (e.g., a structure optimization)

Additionally, there's one extra file:

- `conftest`: Runs Simmate tests and is intended solely for contributing developers
