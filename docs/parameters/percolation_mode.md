## percolation_mode
This parameter sets the percolating type to detect. The default is ">1d", which searches for percolating paths up to the `max_path_length`. Alternatively, this can be set to "1d" to stop unique pathway finding when 1D percolation is achieved.

=== "yaml"
    ``` yaml
    percolation_mode: 1d
    ```
=== "toml"
    ``` toml
    percolation_mode = "1d"
    ```
=== "python"
    ``` python
    percolation_mode = "1d"
    ```
