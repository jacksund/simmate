
# chemical_system

This parameter specifies the chemical system to be used in the analysis. It should be given as a string in the format `Element1-Element2-Element3-...`. For example, `Na-Cl`, `Y-C`, and `Y-C-F` are valid chemical systems.

=== "yaml"
    ``` yaml
    chemical_system: Na-Cl
    ```
=== "toml"
    ``` yaml
    chemical_system = "Na-Cl"
    ```
=== "python"
    ``` python
    chemical_system = "Na-Cl"
    ```

!!! warning
    Some workflows only accept a chemical system with a specific number of elements.
    An example of this is the `structure-prediction.python.binary-composition` search
    which only allows two elements (e.g. `Y-C-F` would raise an error)
