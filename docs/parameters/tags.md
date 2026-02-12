## tags

When submitting workflows via the `run_cloud` command, tags are 'labels' that help control which workers are allowed to pick up and run the submitted workflow. Workers should be started with matching tags in order for these scheduled flows to run.

When no tags are set, the following default tags will be used for a Simmate workflow:

- [x] `simmate` (this is the default worker tag as well)
- [x] the workflow's type name
- [x] the workflow's app name
- [x] the full workflow name

For example, the `static-energy.vasp.matproj` would have the following tags:
``` yaml
- simmate
- static-energy
- vasp
- static-energy.vasp.matproj
```

To override these default tags, use the following:

=== "yaml"
    ``` yaml
    tags:
        - my-tag-01
        - my-tag-02
    ```
=== "toml"
    ``` toml
    tags = ["my-tag-01", "my-tag-02"]
    ```
=== "python"
    ``` python
    tags = ["my-tag-01", "my-tag-02"]
    ```

!!! warning
    When you have a workflow that is submitting many smaller workflows (such as 
    `structure-prediction` workflows), make sure you set the tags in the
    `subworkflow_kwargs` settings:
    ``` yaml
    subworkflow_kwargs:
        tags:
            - my-tag-01
            - my-tag-02
    ```

!!! bug
    Filtering tags does not always work as expected in SQLite3 because a worker with 
    `my-tag` will incorrectly grab jobs like `my-tag-01` and `my-tag-02`. This
    issue is known by both [Django](https://docs.djangoproject.com/en/4.2/ref/databases/#substring-matching-and-case-sensitivity) and [SQLite3](https://www.sqlite.org/faq.html#q18). Simmate addresses this issue by requiring all
    tags to be 7 characters long AND fully lowercase when using SQLite3.
