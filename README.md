<!-- Simmate Logo -->
<p align="center" href=https://simmate.org>
   <img src="https://github.com/jacksund/simmate/blob/main/src/simmate/website/core_components/static/images/simmate-logo-dark.svg?raw=true" width="700" style="max-width: 700px;">
</p>

## About

Simmate is a full-stack framework for chemistry research. It helps you calculate properties and explore third-party databases for both for molecular and crystalline systems. It also provides a toolbox to build out your own chemistry applications.

To be more precise for experienced devs... this repo is essentially a collection of chemistry-based [Django](https://www.djangoproject.com/) apps that are built out using our custom toolkit. At the lowest level, the toolkit acts a wrapper+extension of [pymatgen](https://pymatgen.org/) and [rdkit](https://www.rdkit.org/). Meanwhile, our frontend framework is built on top of [htmx](https://htmx.org/) to make pages dynamic, while the database backend uses [sqlite](https://sqlite.org/) as the default for beginners + [postgres](https://www.postgresql.org/) for production systems. There is a lot more built in to the codebase (including a custom workflow orchestration system) so make sure you explore!

## Before exploring the code

This Github repo holds all of our source code. Before getting started here, you may way to check out...

- our main website at [simmate.org](https://simmate.org/)
- our tutorials, docs, and changelog at [jacksund.github.io/simmate](https://jacksund.github.io/simmate/home/)

## Ready to jump in?

You can install Simmate using either [uv](https://docs.astral.sh/uv/getting-started/installation/) or [conda](https://conda-forge.org/download/): 
``` bash
uv pip install simmate
```
``` bash
conda install -c conda-forge simmate
```

## Need help or have a suggestion?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 

## Citing

<a href="https://doi.org/10.21105/joss.04364">
    <img src="https://img.shields.io/badge/-DOI:10.21105/joss.04364-00666b">
</a>
