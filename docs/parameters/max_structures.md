## max_structures
For workflows that generate new structures (and potentially run calculations on them), this will be the maximum number of structures allowed. The workflow will end at this number of structures regardless of whether the calculation/search is converged or not.

=== "yaml"
    ``` yaml
    max_structures: 100
    ```
=== "toml"
    ``` toml
    max_structures = 100
    ```
=== "python"
    ``` python
    max_structures = 100
    ```
