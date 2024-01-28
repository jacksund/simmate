# Installation

## Quick Start

1. Download and install [anaconda](https://www.anaconda.com/products/distribution)

2. Set up a conda environment, install Simmate within it, and activate it. *(Note: We recommend using Spyder as your IDE, but it's not mandatory)*
``` shell
conda create -n my_env -c conda-forge python=3.11 simmate
conda install -n my_env -c conda-forge spyder  # optional but recommended
conda activate my_env
```

    !!! tip
        If the environment takes more than 2 minutes to resolve, you might be using an outdated version of conda. Ensure your conda version is updated ([>=23.10.0](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community)) to utilize the new [libmamba solver](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community).
    
    !!! info
        Simmate is also available via `pip install simmate`, but because of our many dependencies, we recommend sticking with `conda`.

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
