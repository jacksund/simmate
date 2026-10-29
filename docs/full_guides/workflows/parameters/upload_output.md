This parameter determines whether to upload the results to your S3 bucket (`settings.s3.bucket`) at the end of the run. If [`compress_output`](compress_output.md) is also set, the zip file is uploaded. Otherwise, the full `directory` is uploaded. Results are stored under `workflow_runs/<workflow-name>/<run_id>`. Results are only uploaded when the run succeeds. The default is False.

=== "yaml"
    ``` yaml
    upload_output: true
    ```
=== "toml"
    ``` toml
    upload_output = true
    ```
=== "python"
    ``` python
    upload_output = True
    ```
