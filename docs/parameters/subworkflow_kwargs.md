
This parameter is a dictionary of parameters to pass to each subworkflow run. For example, the workflow will be ran as `subworkflow.run(**subworkflow_kwargs)`. Note, many workflows that use this argument will automatically pass information that is unique to each call (such as `structure`).

=== "yaml"
    ``` yaml
    subworkflow_kwargs:
        command: mpirun -n 4 vasp_std > vasp.out
        compress_output: true
    ```
=== "toml"
    ``` toml
    [subworkflow_kwargs]
    command = "mpirun -n 4 vasp_std > vasp.out"
    compress_output = true
    ```
=== "python"
    ``` python
    subworkflow_kwargs=dict(
        command="mpirun -n 4 vasp_std > vasp.out",
        compress_output=True,
    )
    ```
