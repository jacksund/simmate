# Installation

## Quick Start

1. Download and install [anaconda](https://www.anaconda.com/products/distribution)

    !!! warning
        Anaconda requires a license if you work at a company with >200 employees (academic instituitions exlcuded). If this applies to you, download [miniforge](https://github.com/conda-forge/miniforge) instead, which is free & open-source for everyone. The conda commands below will be the same.

2. Set up a conda environment, install Simmate within it, and activate it
``` shell
conda create -n my_env -c conda-forge python=3.11 simmate
conda activate my_env
```

3. Run the help command to verify the installation
``` bash
simmate --help
```

4. For first-time setup, initialize your local database (SQLite)
``` bash
simmate database reset
```

5. Start the local dev server and keep this command running
``` bash
simmate run-server
```

6. Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to access your local server
