## copy_previous_directory
This parameter determines whether to copy the directory from the previous calculation (if one exists) and use it as a starting point for the new calculation. This is only possible if you provided an input that points to a previous calculation. For instance, `structure` would need to use a database-like input:

=== "yaml"
    ``` yaml
    structure:
        database_table: Relaxation
        database_id: 123
    copy_previous_directory: true
    ```
=== "toml"
    ``` toml
    copy_previous_directory: true

    [structure]
    database_table = "Relaxation"
    database_id = 123
    ```
=== "python"
    ``` python
    structure = {"database_table": "Relaxation", "database_id": 123}
    copy_previous_directory=True
    ```
