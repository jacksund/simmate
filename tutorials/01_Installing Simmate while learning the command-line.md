This tutorial will include...
- installing anaconda
- intro to the GUI
- intro the command-line
- creating a custom enviornment
- installing simmate and spyder


### to create conda env...
conda create -n simmate -c conda-forge python=3.8 numpy pandas django prefect dask click django-crispy-forms django-pandas psycopg2 dask-jobqueue scikit-learn pytest matplotlib plotly pymatgen spyder graphviz pygraphviz dj-database-url djangorestframework django-filter django-extensions pyyaml gunicorn numba

### pymatgen-diffusion is outdated on anaconda
pip install pymatgen-analysis-diffusion

### other packages for pulling data
pip install jarvis-tools

# git clone https://github.com/jacksund/simmate.git
pip install -e simmate
