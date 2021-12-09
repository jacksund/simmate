# Installing Simmate while Learning the Command-line

> A quick comment on tutorials... All tutorials will have two sections: a short-and-to-the-point one for experts and a much longer one for beginners. The critical steps in each are **exactly the same**. However, the full tutorial includes extra exploration of the software and how to use it. For example, this tutorial includes a guide on the command-line as well as concepts of python enviornments and working directories. Be sure to read the full tutorials if you don't have coding experience!

## The quick version

1. Install [anaconda](https://www.anaconda.com/products/individual-d)
2. Create a conda enviornment, install Simmate in it, and activate it. *(note: Spyder is optional but recommended)*
```
conda create -n my_env -c conda-forge python=3.8 simmate spyder
conda activate my_env
```
3. Run the `simmate` command to make sure it's installed correctly

## The full tutorial

- installing anaconda
- intro to the GUI
- intro the command-line
- creating a custom enviornment
- installing simmate and spyder


> :warning: the conda install is not ready yet. For now I install all dependencies manually and then do a dev install of simmate. You do this with the following commands:
```bash
# Create conda enviornment and activate it
conda create -n my_env -c conda-forge python=3.8 numpy pandas django prefect dask click django-crispy-forms django-pandas psycopg2 dask-jobqueue scikit-learn pytest matplotlib plotly pymatgen spyder graphviz pygraphviz dj-database-url djangorestframework django-filter django-extensions pyyaml gunicorn numba matminer gh;
conda activate my_env;

# (optional) Install extra utiliities that aren't available on conda-forge
pip install pymatgen-analysis-diffusion;
pip install jarvis-tools;

# Download the source-code and install it in an "editable" (-e) fashion
git clone https://github.com/jacksund/simmate.git;
pip install -e simmate;
```
