# Getting Started

!!! tip "New to git?"
    [GitKraken](https://www.gitkraken.com/) lets you fork, clone, branch, and commit without the command line. Their [6-minute intro video](https://www.youtube.com/watch?v=ub9GfRziCtU) covers the basics. Students and teachers get GitKraken Pro and GitHub Pro free through [GitHub Education](https://education.github.com/).

1. Fork and clone [jacksund/simmate](https://github.com/jacksund/simmate):
    - **GitKraken:** fork the repo on GitHub, then clone your fork (`yourname/simmate`) in GitKraken
    - **GitHub CLI:** `gh repo fork jacksund/simmate --clone` (also adds `jacksund/simmate` as the `upstream` remote)

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then create the virtual environment and install all dependencies:
    ``` shell
    cd simmate
    uv sync --all-extras
    ```

3. Activate the virtual environment:

    === "macOS & Linux"
        ``` bash
        source .venv/bin/activate
        ```

    === "Windows"
        ``` powershell
        .venv\Scripts\activate
        ```

4. Start from a fresh, empty database:
    ``` shell
    simmate database reset --confirm-delete --no-use-prebuilt
    ```

5. Make sure the tests pass:
    ``` shell
    simmate dev test
    ```

6. Continue to [Creating & submitting changes](creating_and_submitting_changes.md) for linting, testing, and opening a pull request.
