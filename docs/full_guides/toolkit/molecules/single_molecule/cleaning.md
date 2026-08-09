# Molecule Cleaning & Method Preparation

--------------------------------------------------------------------------------

## Hydrogens (Implicit vs. Explicit)

The `add_hydrogens` and `remove_hydrogens` methods are used to add and remove Hydrogens. These methods are applicable only to Hydrogens that can be inferred from the base structure:

=== "Add Hydrogens"
    ``` python
    molecule.add_hydrogens()
    ```

=== "Remove Hydrogens"
    ``` python
    molecule.remove_hydrogens()
    ```


!!! tip
    Hydrogens are typically not present but "implied" in 2D molecules (e.g. SMILES). However, certain analyses and methods require explicit Hydrogens for accuracy, such as 3D conformer generation.

    Many methods and workflows automatically add Hydrogens when necessary. This is particularly useful when optimizing scripts for large molecule sets (>10k).

--------------------------------------------------------------------------------

## Fragments / Mixtures

Several methods are available to parse a "molecule" that is actually a mixture (i.e., contains more than one molecule or species).

``` python
mixture = Molecule.from_sdf("example.sdf")

for molecule in mixture.get_fragments():
    print(molecule.to_smiles())
```

| METHOD                        |
| ----------------------------- |
| `get_largest_fragment`        |
| `split_fragments` (UNDER DEV) |
| `num_fragments` (UNDER DEV) |
| `get_fragments` (UNDER DEV) |

!!! warning
    These methods may be removed as conformers should be separate `Molecule` objects.

--------------------------------------------------------------------------------

## Stereochemistry

!!! warning
    Stereochemistry cleanup is currently under development. In the meantime, consider using tools like "Flipper" to iterate stereochemistry.

--------------------------------------------------------------------------------

## 2D to 3D Conversion

Molecules are often provided as 2D representations, which are human-readable and can be drawn on paper (as a Lewis structure). However, simulations usually require 3D representations to accurately depict the molecule's real-life shape.

The `convert_to_3d` method is a simple strategy to generate "reasonable" 3D coordinates for a molecule:

``` python
molecule.convert_to_3d()
```

!!! danger
    The generation of 3D conformers is a complex topic with various strategies. The method shown here is the simplest and quickest approach. We plan to expand this section in the future to discuss different workflows and their respective advantages and disadvantages.

    We may also update the `convert_to_3d` method to accept different workflow names (e.g., using either surflex or omega apps).

--------------------------------------------------------------------------------