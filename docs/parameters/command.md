
This parameter specifies the command that will be called during the execution of a program. There is typically a default set for this that you only need to change if you'd like parallelization. For example, VASP workflows use `vasp_std > vasp.out` by default but you can override this to use `mpirun`.

=== "yaml"
    ``` yaml
    command: mpirun -n 8 vasp_std > vasp.out
    ```
=== "toml"
    ``` toml
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```
=== "python"
    ``` python
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```
