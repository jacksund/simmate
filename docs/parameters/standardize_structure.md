## standardize_structure
This parameter determines whether to standardize the structure during our setup(). This means running symmetry analysis on the structure to reduce the symmetry and convert it to some standardized form. There are three different forms to choose from and thus 3 different values that `standardize_structure` can be set to:

- `primitive`: for the standard primitive unitcell
- `conventional`: for the standard conventional unitcell
- `primitive-LLL`: for the standard primitive unitcell that is then LLL-reduced
- `False`: this is the default and will disable this feature

We recommend using `primitive-LLL` when the smallest possible and most cubic unitcell is desired.

We recommend using `primitive` when calculating band structures and ensuring we have a standardized high-symmetry path. Note,Existing band-structure workflows use this automatically.

To control the tolerances used to symmetrize the structure, you can use the symmetry_precision and angle_tolerance attributes.

By default, no standardization is applied.

=== "yaml"
    ``` yaml
    standardize_structure: primitive-LLL
    ```
=== "toml"
    ``` toml
    standardize_structure = "primitive-LLL"
    ```
=== "python"
    ``` python
    standardize_structure = "primitive-LLL"
    ```
