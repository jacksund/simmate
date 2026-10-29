
This is the directory where everything will be run -- either as a relative or full path. If not provided, a folder named after the workflow's `run_id` is made inside your `scratch_dir` setting (such as `3a1bd23f-705c-4947-96fa-3740865ed12d`). This matches the `run_id` in your database and the key used when uploading results to S3. This will be converted into a `pathlib.Path` object. Accepted inputs include:

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
