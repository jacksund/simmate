
## Check your installed version

When importing simmate and establishing a connection to the database, a warning message will be displayed if your version is not the most recent one. You can also verify this via the command-line:

``` bash
simmate version
```


## Upgrading to the Latest Version

We strongly advise installing Simmate in a fresh environment instead of updating it within your current one. 

For **conda** users:
``` shell
conda create -n my_env -c conda-forge python=3.11 simmate
```

For **uv** users:
``` shell
uv venv
source .venv/bin/activate
uv pip install simmate
```

Ensure that the expected version is installed:
``` bash
simmate version
```

Update your database to be compatible with the new installation:
``` bash
simmate database update
```

!!! danger "Database Compatibility"
    Simmate's API is currently in development (`v0.*.*`), and database migrations are only supported within specific version ranges. The `simmate database update` command is effective for:

    - **v0.19.0 to Latest**: Fully compatible
    - **v0.15.0 to v0.18.0**: Compatible within this range only
    - **v0.0.0 to v0.14.0**: Incompatible (the update command did not exist)

    Upgrading between these groups (e.g., from v0.18.0 to v0.19.0) requires `simmate database reset`. If you need assistance migrating data across incompatible versions, please reach out to our team.


## Understanding Version Numbers

Our releases follow [semantic versioning](https://semver.org/). This implies that versions (e.g., `v1.2.3`) correspond to `MAJOR.MINOR.PATCH`. Each version number increases following these changes:

  - `MAJOR` = incompatible API changes
  - `MINOR` = addition of new functionality (without API changes)
  - `PATCH` = bug fixes and documentation updates (without API changes)

There is one significant exception to the above rules -- `MAJOR=0` releases. Any `v0.x.y` release is considered developmental, where APIs are subject to change and are not deemed stable.

