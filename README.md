<!-- Simmate Logo -->
<p align="center">
   <a href="https://simmate.org">
      <img src="https://raw.githubusercontent.com/jacksund/simmate/refs/heads/main/src/simmate/website/core/static/images/simmate-logo.svg" width="550" style="max-width: 550px;">
   </a>
</p>

<!-- Links -->
<p align="center">
   Website: <a href="https://simmate.org/">simmate.org</a> | Tutorials &amp; Docs: <a href="https://jacksund.github.io/simmate/home/">jacksund.github.io/simmate</a> | Paper: <a href="https://doi.org/10.21105/joss.04364">doi.org/10.21105/joss.04364</a>
</p>

<!-- Desktop App Screenshot -->
<p align="center">
   <img src="https://raw.githubusercontent.com/jacksund/simmate/refs/heads/main/src/simmate/website/core/static/images/desktop-toolkit.png" alt="Simmate Desktop's Toolkit tab filtering a compound dataset by substructure" width="900">
</p>

## About

Simmate is a full-stack framework and ecosystem for chemistry research, covering both molecular and crystalline systems. It brings dozens of popular programs and databases together under one consistent interface, and gives you the building blocks to make your own chemistry applications. Out of the box, Simmate provides:

- **Chemical toolkit**: Pythonic `Molecule` and `Structure` objects built on RDKit and pymatgen, plus featurizers, similarity metrics, clustering, and predictive models.
- **Desktop app**: a cross-platform app for exploring and filtering datasets and managing workers.
- **Database & ORM**: Django-based tables with standard chemistry columns, which you can query from Python, SQL, the web UI, or a REST API (SQLite locally, PostgreSQL in production).
- **Datastores**: parquet-backed storage for datasets with millions of rows, with fast filtering and vector-indexed similarity search.
- **Website**: a Django + htmx web UI for browsing data, submitting workflows, and viewing results.
- **Compute orchestration**: run jobs anywhere from a laptop to SLURM clusters or Kubernetes, with workers that pull jobs from a shared database.
- **Workflow library**: ready-to-use workflows for VASP, Quantum ESPRESSO, Bader analysis, evolutionary structure prediction, and more.
- **Built-in datasets**: ready-to-load data from Materials Project, COD, JARVIS, OQMD, AFLOW, ChEMBL, Enamine, and more.

## Installation

Install with our one-line installer (it also sets up [uv](https://docs.astral.sh/uv/) if needed):
```bash
# macOS & Linux
curl -LsSf https://simmate.org/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://simmate.org/install.ps1 | iex"
```

To import Simmate in your own Python scripts, install it into an environment using either [uv](https://docs.astral.sh/uv/getting-started/installation/) or [conda](https://conda-forge.org/download/) instead:
```bash
uv pip install simmate
# or
conda install -c conda-forge simmate
```

## Quickstart

Once installed, try out these commands:
```bash
# view all available commands
simmate --help

# launch the desktop app
simmate desktop start

# set up your database, then launch the web UI (at http://localhost:8000/)
simmate database reset
simmate website start
```

To learn more, continue with [our tutorials](https://jacksund.github.io/simmate/getting_started/introduction/).

## Need help?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 
