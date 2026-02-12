## directory
This is the directory where everything will be run -- either as a relative or full path. This is passed to the utilities function `simmate.ulitities.get_directory`, which generates a unique folder name if not provided (such as `simmate-task-12390u243`). This will be converted into a `pathlib.Path` object. Accepted inputs include:

**leave as default (recommended)**

**a string**

=== "yaml"
    ``` yaml
    directory: my-new-folder-00
    ```
=== "toml"
    ``` toml
    directory = "my-new-folder-00"
    ```
=== "python"
    ``` python
    directory = "my-new-folder-00"
    ```


**a `pathlib.Path` (best for advanced logic)**

=== "python"
    ``` python
    from pathlib import Path
    
    directory = Path("my-new-folder-00")
    ```
