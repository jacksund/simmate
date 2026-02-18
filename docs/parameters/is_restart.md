
(experimental feature)
This parameter indicates whether the calculation is a restarted workflow run. The default is False. If set to true, the workflow will go through the given directory (which must be provided) and determine where to resume.

=== "yaml"
    ``` yaml
    directory: my-old-calc-folder
    is_restart: true
    ```
=== "toml"
    ``` toml
    directory = "my-old-calc-folder"
    is_restart = true
    ```
=== "python"
    ``` python
    directory = "my-old-calc-folder"
    is_restart = True
    ```
