
The number of images (or structures) to use in the analysis. This does NOT include the endpoint images (start/end structures). More is better, but computationally expensive. We recommend keeping this value odd in order to ensure there is an image at the midpoint.

=== "yaml"
    ``` yaml
    nimages: 5
    ```
=== "toml"
    ``` toml
    nimages = 5
    ```
=== "python"
    ``` python
    nimages = 5
    ```

!!! danger
    For apps such as VASP, your `command` parameter must use a number of cores that is divisible by `nimages`. For example, `nimages=3` and `command="mpirun -n 10 vasp_std > vasp.out"` will fail because 10 is not divisible by 3.
