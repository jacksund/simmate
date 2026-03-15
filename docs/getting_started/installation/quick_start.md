# Installation

## Quick Start

1. Download and install your preferred package manager:

    === "uv (Recommended)"
        Visit the [uv installation page](https://docs.astral.sh/uv/getting-started/installation/) and follow the instructions for your operating system.

    === "Anaconda / Miniforge"
        Visit the [Anaconda download page](https://www.anaconda.com/products/distribution) or [Miniforge page](https://github.com/conda-forge/miniforge) and install.

        !!! warning
            Anaconda requires a license for companies with >200 employees (academic institutions are excluded). If this applies to you, use Miniforge instead.

2. Create a virtual environment and install Simmate:

    === "uv"
        ``` bash
        uv venv my_env
        source my_env/bin/activate  # On Windows use: my_env\Scripts\activate
        uv pip install simmate
        ```

    === "conda"
        ``` bash
        conda create -n my_env -c conda-forge python=3.11 simmate
        conda activate my_env
        ```

3. Verify the installation:
    ``` bash
    simmate --help
    ```
