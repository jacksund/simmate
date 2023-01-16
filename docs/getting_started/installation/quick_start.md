# Installation

In this tutorial, you will learn how to install Simmate with Anaconda and start up a local server. Beginners will also be introduced to the command-line.

!!! danger
    In this tutorial and others, **beginners without coding experience should skip the quick-start tutorial** section and jump straight to the full tutorial. *The critical steps in each are exactly the same*, but the full tutorial includes extra exploration of the software and how to use it.

----------------------------------------------------------------------

## Quick start

1. Install [anaconda](https://www.anaconda.com/products/distribution)
2. Create a conda environment, install Simmate in it, and activate it. *(note: Spyder is our recommended IDE but optional)*
``` shell
conda create -n my_env -c conda-forge python=3.11 simmate
conda install -n my_env -c conda-forge spyder  # optional but recommended
conda activate my_env
```
3. Run the `simmate --help` command to make sure it's installed correctly
4. For first-time setup, initialize your local database with `simmate database reset`
5. Run the command `simmate run-server` (and leave this command running)
6. Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) and you'll see you local server!

Note, this server is only accessible on your local computer. For a production-ready server, see our [website documentation](/full_guides/website/overview/).

!!! note 
    Simmate itself is <2MB, but when installed to a clean conda environment, the entire download for all it's dependencies comes to ~1.2GB. Additional disk space is also needed for optional downloads -- such as [third-party data](/full_guides/database/third_party_data/).

----------------------------------------------------------------------

## Speed-up your installation

### Faster Conda

While it is the recommended way to install Simmate, **conda can be extremely slow**. 
It can take >20 minutes to solve the environment on some systems because of 
Simmate's many large dependencies. 
        
We therefore suggest experienced users try the following:
        
- set `conda config --set channel_priority strict`            
- use the [libmamba](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community) solver

### Mamba

Instead of Anaconda, you could just use [Mamba](https://mamba.readthedocs.io/en/latest/) from the start. In fact, our team uses micromamba for our CI, so this is well tested.
=== "mamba"
    ``` bash
    mamba create -n my_env -c conda-forge python=3.10 simmate
    ```

### Pip

Pip is the default package installer for python, but **be warned** that it can 
cause problems for beginners (especially those on Windows PCs):

=== "pip"
    ``` bash
    pip install simmate
    ```
    
!!! danger
    Pip should only be used as an absolute last resort for installing
    Simmate. Do this only if you are an advanced python user and understand
    how to manage your python env's effectively.

----------------------------------------------------------------------

