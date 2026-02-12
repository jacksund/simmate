## subworkflow_name
This parameter is the name of workflow that used to evaluate structures generated. Any workflow that is registered and accessible via the `get_workflow` utility can be used instead. If you wish to submit extra arguments to each workflow run, you can use the `subworkflow_kwargs` parameter.

=== "yaml"
    ``` yaml
    subworkflow_name: relaxation.vasp.staged
    ```
=== "toml"
    ``` toml
    subworkflow_name = "relaxation.vasp.staged"
    ```
=== "python"
    ``` python
    subworkflow_name = "relaxation.vasp.staged"
    ```
