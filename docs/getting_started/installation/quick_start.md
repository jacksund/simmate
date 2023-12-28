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

!!! note
    Simmate itself is <1MB, but when installed to a clean conda environment, the entire download for Simmate and all it's dependencies comes to ~1GB. Additional disk space is also needed for optional downloads -- such as [third-party data](/full_guides/database/third_party_data/).

!!! tip
    If it takes >2 minutes to solve the environment,
    then you are likely using an outdated version of conda.

    Make sure to update your conda version ([>=23.10.0](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community))
    so that it is using the new 
    [libmamba solver](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community

----------------------------------------------------------------------
