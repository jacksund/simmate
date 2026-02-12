## composition
The composition input can be anything compatible with the `Composition` toolkit class. Note that compositions are sensitive to atom counts / multiplicity. There is a difference between giving `Ca2N` and `Ca4N2` in several workflows. Accepted inputs include:

**a string (recommended)**

=== "yaml"
    ``` yaml
    composition: Ca2NF
    ```
=== "toml"
    ``` toml
    composition = "Ca2NF"
    ```
=== "python"
    ``` python
    composition = "Ca2NF"
    ```

**a dictionary that gives the composition**

=== "yaml"
    ``` yaml
    composition:
        Ca: 2
        N: 1
        F: 1
    ```
=== "toml"
    ``` yaml
    [composition]
    Ca = 2
    N = 1
    F = 1
    ```
=== "python"
    ``` python
    composition={
        "Ca": 2, 
        "N": 1, 
        "F": 1,
    }
    ```

**a `Composition` object (best for advanced logic)**

=== "python"
    ``` python
    from simmate.toolkit import Compositon
    
    composition = Composition("Ca2NF")
    ```
