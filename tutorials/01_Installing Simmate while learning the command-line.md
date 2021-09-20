# Installing Simmate while Learning the Command-line

> :warning: the conda install is not ready yet. For now I install all dependencies manually and then do a dev install of simmate. You do this with the following commands:
```bash
# Create conda enviornment and activate it
conda create -n my_env -c conda-forge python=3.8 numpy pandas django prefect dask click django-crispy-forms django-pandas psycopg2 dask-jobqueue scikit-learn pytest matplotlib plotly pymatgen spyder graphviz pygraphviz dj-database-url djangorestframework django-filter django-extensions pyyaml gunicorn numba;
conda activate my_env;

# (optional) Install extra utiliities that aren't available on conda-forge
pip install pymatgen-analysis-diffusion;
pip install jarvis-tools;

# Download the source-code and install it in an "editable" (-e) fashion
git clone https://github.com/jacksund/simmate.git;
pip install -e simmate;
```

### A quick comment on tutorials

All tutorials will have two sections: a short-and-to-the-point one for experts and a much longer one for beginners. The steps in each are **exactly the same** -- we just include extra explanation for beginners in the longer tutorial. 

## The quick version

1. Install [anaconda](https://www.anaconda.com/products/individual-d)
2. Create a conda enviornment, install Simmate in it, and activate it. *(note: Spyder is optional but recommended)*
```
conda create -n my_env -c conda-forge python=3.8 simmate spyder
conda activate my_env
```
4. Run the `simmate` command to make sure it's installed correctly
5. Initialize our Simmate database with `simmate databate reset`
6. Start the simmate test server with `simmate run-server`
7. You can now view the web UI at http://127.0.0.1:8000/

## The full tutorial

- installing anaconda
- intro to the GUI
- intro the command-line
- creating a custom enviornment
- installing simmate and spyder
