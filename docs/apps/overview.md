
## What is an App?

Apps are installable Simmate add-ons. Each one adds support for a third-party software/dataset or helps with a specific analysis. Learn more in the [`Apps` section within the `Full Guides`](/full_guides/apps/basic_use.md).

!!! example
    VASP is a program capable of running a variety of density functional theory (DFT) calculations. However, since it's not written in Python, we require some "helper" code to execute VASP commands, create input files, and extract data from the outputs. This helper code is what makes up Simmate's `vasp` app.

!!! example
    The `evolution` app includes workflows for running evolutionary structure prediction. It also utilizies datasets from other data-providing apps like `oqmd`, `jarvis`, and `aflow` into the evolutionary searches.

## Summary Table

| App                   | Type                              | CLI                | Workflows          | Data               |
| --------------------- | --------------------------------- | ------------------ | ------------------ | ------------------ |
| AFLOW                 | :simple-crystal: `crystal`        | --                 | --                 | :white_check_mark: |
| BadELF                | :simple-crystal: `crystal`        | --                 | --                 | :white_check_mark: |
| Bader (henkelman)     | :simple-crystal: `crystal`        | --                 | :white_check_mark: | --                 |
| BCPC                  | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| CAS Registry          | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| ChEMBL                | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| ChemSpace             | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| COD                   | :simple-crystal: `crystal`        | --                 | --                 | :white_check_mark: |
| eMolecules            | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| Enamine               | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| EPPO Global Database  | :material-beaker-outline: `other` | --                 | --                 | :white_check_mark: |
| Evolutionary Searches | :simple-crystal: `crystal`        | --                 | :white_check_mark: | --                 |
| JARVIS                | :simple-crystal: `crystal`        | --                 | --                 | :white_check_mark: |
| Materials Project     | :simple-crystal: `crystal`        | --                 | :white_check_mark: | :white_check_mark: |
| OQMD                  | :simple-crystal: `crystal`        | --                 | --                 | :white_check_mark: |
| PDB                   | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| PPDB                  | :simple-moleculer: `molecule`     | --                 | --                 | :white_check_mark: |
| Quantum Espresso      | :simple-crystal: `crystal`        | :white_check_mark: | :white_check_mark: | --                 |
| RDKit                 | :simple-moleculer: `molecule`     | --                 | --                 | --                 |
| VASP                  | :simple-crystal: `crystal`        | :white_check_mark: | :white_check_mark: | --                 |
| Warren Lab            | :simple-crystal: `crystal`        | --                 | :white_check_mark: | :white_check_mark: |
