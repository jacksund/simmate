## max_supercell_atoms
For workflows that involve generating a supercell, this will be the maximum number of sites to allow in the generated structure(s). For example, NEB workflows would set this value to something like 100 atoms to limit their supercell image sizes.

=== "yaml"
    ``` yaml
    max_supercell_atoms: 100
    ```
=== "toml"
    ``` toml
    max_supercell_atoms = 100
    ```
=== "python"
    ``` python
    max_supercell_atoms = 100
    ```
