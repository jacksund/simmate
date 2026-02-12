# Workflow Parameters


### About

This section provides a detailed overview of all unique parameters for all workflows.

To identify the parameters allowed for a specific workflow, use the `explore` command or `workflow.show_parameters()`:

=== "command line"
    ``` bash
    simmate workflows explore
    ```

=== "python"

    ``` python
    workflow.show_parameters()
    ```

### File vs. Python formats

When switching from Python to YAML, make sure you adjust the input format of your parameters. This is especially important if you use python a `list` or `dict` for one of your input parameters. Further, if you have complex input parameters (e.g. nested lists, matricies, etc.), we recommend using a TOML input file instead:

=== "lists"
    ``` python
    # in python
    my_parameter = [1,2,3]
    ```
    ``` yaml
    # in yaml
    my_parameter:
        - 1
        - 2
        - 3
    ```

=== "dictionaries"
    ``` python
    # in python
    my_parameter = {"a": 123, "b": 456, "c": ["apple", "orange", "grape"]}
    ```
    ``` yaml
    # in yaml
    my_parameter:
        a: 123
        b: 456
        c:
            - apple
            - orange
            - grape
    ```
    ``` toml
    # in toml
    [my_parameter]
    a = 123
    b = 456
    c = ["apple", "orange", "grape"]
    ```

=== "nested lists"
    ``` python
    # in python
    my_parameter = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    ```
    ``` yaml
    # in yaml (we recommend switching to TOML!)
    my_parameter:
        - - 1
            - 2
            - 3
        - - 4
            - 5
            - 6
        - - 7
            - 8
            - 9
    ```
    ``` toml
    # in toml
    my_parameter = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    ```

=== "tuple"
    ``` python
    # in python
    my_parameter = (1,2,3)
    ```
    ``` yaml
    # in yaml
    my_parameter:
        - 1
        - 2
        - 3
    # WARNING: This will return a list! Make sure you call 
    #   `tuple(my_parameter)`
    # at the start of your workflow's `run_config` if you need a tuple.
    ```
    ``` toml
    # in toml
    my_parameter = [1, 2, 3]
    # WARNING: This will return a list! Make sure you call 
    #   `tuple(my_parameter)`
    # at the start of your workflow's `run_config` if you need a tuple.
    ```
