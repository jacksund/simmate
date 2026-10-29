
This parameter determines whether to compress the `directory` to a zip file at the end of the run. The original directory is kept, so set [`delete_output`](delete_output.md) as well if you want it removed. The default is False.

=== "yaml"
    ``` yaml
    compress_output: true
    ```
=== "toml"
    ``` toml
    compress_output = true
    ```
=== "python"
    ``` python
    compress_output = True
    ```
