
# Creating our environment and installing Simmate

For now, let's create a new environment that uses the [conda-forge](https://conda-forge.org/) channel. A channel is where anaconda downloads packages from -- and to keep things simple, we will ALWAYS use conda-forge (this is the standard in the python community). 

----------------------------------------------------------------------

## 1. Create the environment

Now let's run this command below. Note you can switch out the name `my_env` for whatever you want here, just make sure you use underscores instead of spaces (`my_env` will work while `my env` will give an error).

``` shell
conda create -c conda-forge -n my_env python=3.10
```

Say yes when the installation asks for confirmation. 

----------------------------------------------------------------------

## 2. Activate the environment
Next, switch to this new environment. To do that we use...

``` shell
conda activate my_env
```

You'll see the start of your command line switch from `(base)` to `(my_env)` if this worked successfully. 

----------------------------------------------------------------------

## 3. Install Simmate
Next, we want to install Simmate.

``` shell
conda install -c conda-forge -n my_env simmate
```

This may take a few minutes to run and install. But once it's done, you've now successfully installed Simmate! If you ran into any errors with this very last command, please let our team know immediately by [posting a new issue here](https://github.com/jacksund/simmate/issues/).

----------------------------------------------------------------------

## 4. Install Spyder

As an extra, let's use Anaconda to install [Spyder](https://www.spyder-ide.org/). Spyder is what we will use to write python in later tutorials. But now that we have Anaconda set up, installing new programs can be done in just one line:
``` shell
conda install -c conda-forge -n my_env spyder
```

----------------------------------------------------------------------
