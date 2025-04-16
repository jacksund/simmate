
## What is an App?

Apps are installable Simmate add-ons. Each one adds support for a third-party software/dataset or helps with a specific analysis. Learn more in the [`Apps` section within the `Full Guides`](/full_guides/apps/basic_use.md).

!!! example
    VASP is a program capable of running a variety of density functional theory (DFT) calculations. However, since it's not written in Python, we require some "helper" code to execute VASP commands, create input files, and extract data from the outputs. This helper code is what makes up Simmate's `vasp` app.

!!! example
    The `evolution` app includes workflows for running evolutionary structure prediction. It also utilizies datasets from other data-providing apps like `oqmd`, `jarvis`, and `aflow` into the evolutionary searches.

## Summary Table

| App                   | Type       | CLI                | Workflows          | Data               |
| --------------------- | ---------- | ------------------ | ------------------ | ------------------ |
| AFLOW                 | `crystal`  | :x:                | :x:                | :white_check_mark: |
| BadELF                | `crystal`  | :x:                | :x:                | :white_check_mark: |
| Bader (henkelman)     | `crystal`  | :x:                | :white_check_mark: | :x:                |
| BCPC                  | `molecule` | :x:                | :x:                | :white_check_mark: |
| CAS Registry          | `molecule` | :x:                | :x:                | :white_check_mark: |
| ChEMBL                | `molecule` | :x:                | :x:                | :white_check_mark: |
| ChemSpace             | `molecule` | :x:                | :x:                | :white_check_mark: |
| COD                   | `crystal`  | :x:                | :x:                | :white_check_mark: |
| eMolecules            | `molecule` | :x:                | :x:                | :white_check_mark: |
| Enamine               | `molecule` | :x:                | :x:                | :white_check_mark: |
| EPPO Global Database  | `other`    | :x:                | :x:                | :white_check_mark: |
| Evolutionary Searches | `crystal`  | :x:                | :white_check_mark: | :x:                |
| JARVIS                | `crystal`  | :x:                | :x:                | :white_check_mark: |
| Materials Project     | `crystal`  | :x:                | :white_check_mark: | :white_check_mark: |
| OQMD                  | `crystal`  | :x:                | :x:                | :white_check_mark: |
| PDB                   | `molecule` | :x:                | :x:                | :white_check_mark: |
| Quantum Espresso      | `crystal`  | :white_check_mark: | :white_check_mark: | :x:                |
| RDKit                 | `molecule` | :x:                | :x:                | :x:                |
| VASP                  | `crystal`  | :white_check_mark: | :white_check_mark: | :x:                |
| Warren Lab            | `crystal`  | :x:                | :white_check_mark: | :white_check_mark: |
