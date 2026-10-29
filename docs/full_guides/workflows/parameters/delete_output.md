This parameter determines whether to delete the `directory` at the end of the run. If a zip file was made (via [`compress_output`](compress_output.md)), the zip file is kept. The directory is only deleted when the run succeeds. The default is False.

=== "yaml"
    ``` yaml
    delete_output: true
    ```
=== "toml"
    ``` toml
    delete_output = true
    ```
=== "python"
    ``` python
    delete_output = True
    ```
