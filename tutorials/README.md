# Simmate Tutorials

Welcome! These tutorials should help you get familiar with Simmate -- whether you're new to coding or an expert user. 

> :warning: Many tutorials are incomplete at the moment, but they'll be finished by the time we release our code to the public.


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