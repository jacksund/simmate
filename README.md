<!-- Simmate Logo -->
<p align="center">
   <a href="https://simmate.org">
      <img src="https://raw.githubusercontent.com/jacksund/simmate/refs/heads/main/src/simmate/website/core/static/images/simmate-logo.svg" width="700" style="max-width: 700px;">
   </a>
</p>

<!-- Links -->
<p align="center">
   Website: <a href="https://simmate.org/">simmate.org</a> | Tutorials &amp; Docs: <a href="https://jacksund.github.io/simmate/home/">jacksund.github.io/simmate</a> | Paper: <a href="https://doi.org/10.21105/joss.04364">doi.org/10.21105/joss.04364</a>
</p>

## About

Simmate is a full-stack framework and ecosystem for chemistry research. It standardizes how researchers interact with dozens of popular tools and databases by providing a robust ORM, workflow library, and a web UI out of the box. For both molecular and crystalline systems, Simmate also provides a comprehensive toolbox to build your own custom chemistry applications.

## Installation

Install with our one-line installer (it also sets up [uv](https://docs.astral.sh/uv/) if needed):
```bash
# macOS & Linux
curl -LsSf https://simmate.org/install.sh | sh
```
```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://simmate.org/install.ps1 | iex"
```

To import Simmate in your own Python scripts, install it into an environment using either [uv](https://docs.astral.sh/uv/getting-started/installation/) or [conda](https://conda-forge.org/download/) instead:
```bash
uv pip install simmate
```
```bash
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

## Need help?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 
