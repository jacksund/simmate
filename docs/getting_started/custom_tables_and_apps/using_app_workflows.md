# Using App Workflows

-------------------------------------------------------------------------------

## Basic use

On the surface, our workflows here behave exactly the same as they did before. We can run them with a yaml file or directly in python.

``` yaml
workflow_name: example_app/workflows:Example__Python__MyExample1
structure: NaCl.cif
input_01: 12345
input_02: true
```

However, now that they are in a Simmate Project and we registered the App, we
can access some extra features. First, we can just use the workflow name and
also access our workflow with the command line and `get_workflow` utilities:

=== "yaml"
    ``` yaml
    workflow_name: example.python.my-example1
    structure: NaCl.cif
    input_01: 12345
    input_02: true
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("example.python.my-example1")
    workflow.run(
        structure="NaCl.cif",
        input_01=,
        input_02=true,
    )
    ```

Check and see your workflow listed now too:
=== "command line"
    ``` bash
    simmate workflows list-all
    ```

-------------------------------------------------------------------------------
