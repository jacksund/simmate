<!-- Simmate Logo -->
<p align="center">
   <a href="https://simmate.org">
      <img src="https://raw.githubusercontent.com/jacksund/simmate/refs/heads/main/src/simmate/website/core/static/images/simmate-logo-dark.svg" width="700" style="max-width: 700px;">
   </a>
</p>

<p align="center">
    <!-- Link to API documentation -->
    <a href="https://jacksund.github.io/simmate/home/">
        <img src="https://img.shields.io/badge/-Tutorials & Docs-/?logo=microsoft-academic&color=00666b&logoColor=white">
    </a>
    <!-- Link to Website -->
    <a href="https://simmate.org/">
        <img src="https://img.shields.io/badge/-Website-/?logo=iCloud&color=00666b&logoColor=white">
    </a>
    <!-- link to JOSS paper -->
    <a href="https://doi.org/10.21105/joss.04364">
        <img src="https://img.shields.io/badge/-DOI:10.21105/joss.04364-00666b">
    </a>
</p>


## About

Simmate is a full-stack framework and ecosystem for chemistry research. It standardizes how researchers interact with dozens of popular tools and databases by providing a robust ORM, workflow library, and a web UI out of the box. For both molecular and crystalline systems, Simmate also provides a comprehensive toolbox to build your own custom chemistry applications.

## Key Features

- **Unified App Ecosystem:** Bridge dozens of third-party datasets (Materials Project, COD, ChEMBL) and software (VASP, Quantum Espresso) through a single, consistent API.
- **Resilient Workflows:** Run complex, multi-step calculations with built-in error handling that automatically detects and fixes common simulation failures.
- **Scalable Orchestration:** Effortlessly schedule and distribute thousands of jobs across local workstations, HPC clusters, or Kubernetes clusters.
- **Scientific Database ORM:** Store, query, and manage your custom workflow results alongside third-party chemistry data using a powerful, built-in Django backend.
- **Batteries-Included UI:** Instantly explore your data, monitor running workflows, and submit new jobs using the integrated web interface and REST API.

**[A preview of features and code snippets is available on our documentation homepage.](https://jacksund.github.io/simmate/home/)**

## Installation

You can install Simmate using either [uv](https://docs.astral.sh/uv/getting-started/installation/) or [conda](https://conda-forge.org/download/):
```bash
uv pip install simmate
```
```bash
conda install -c conda-forge simmate
```

## Need help?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 
