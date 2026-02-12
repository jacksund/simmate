## write_summary_files

This parameter determines whether or not to write output files. For some workflows, writing output files can cause excessive load on the database and possibly make the calculation IO bound. In cases such as this, you can set this to `False`.

=== "yaml"
    ``` yaml
    write_summary_files: false
    ```
=== "toml"
    ``` toml
    write_summary_files = false
    ```
=== "python"
    ``` python
    write_summary_files = False
    ```
    
!!! tip
    Beginners can often ignore this setting. This is typically only relevant
    in a setup where you have many computational resources and have many
    evolutionary searches (>10) running at the same time.
