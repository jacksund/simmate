# Setting Up Your Env & Installing Simmate

To begin, we'll establish a new environment using the [conda-forge](https://conda-forge.org/) channel. Anaconda uses channels to download packages, and for simplicity, we'll consistently use conda-forge, which is a standard practice in the Python community.

----------------------------------------------------------------------

## 1. Environment Creation

Run the command below to create your environment. You can replace `my_env` with any name of your choice, but remember to use underscores instead of spaces (`my_env` is acceptable, `my env` will cause an error).

``` shell
conda create -c conda-forge -n my_env python=3.11
```

Confirm the installation when prompted.

----------------------------------------------------------------------

## 2. Environment Activation

Switch to the newly created environment using the following command:

``` shell
conda activate my_env
```

If it switched successfully, the start of your command line will change from `(base)` to `(my_env)`.

----------------------------------------------------------------------

## 3. Simmate Installation

Now, let's install Simmate:

``` shell
conda install -c conda-forge -n my_env simmate
```

The installation may take a few minutes. Once completed, Simmate is successfully installed! 

If you encounter any errors with this command, please inform our team by [posting a new issue](https://github.com/jacksund/simmate/issues/).

----------------------------------------------------------------------

## 4. Spyder Installation

Lastly, let's install [Spyder](https://www.spyder-ide.org/) using Anaconda. This is optional, but if you're new to coding, you'll need Spyder for writing some Python code in later tutorials:

``` shell
conda install -c conda-forge -n my_env spyder
```

----------------------------------------------------------------------