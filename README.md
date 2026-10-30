<!-- Simmate Logo -->
<p align="center">
   <a href="https://simmate.org">
      <img src="https://raw.githubusercontent.com/jacksund/simmate/refs/heads/main/src/simmate/website/core/static/images/simmate-logo.svg" width="700" style="max-width: 700px;">
   </a>
</p>

## Links

- Tutorials & Docs: [jacksund.github.io/simmate](https://jacksund.github.io/simmate/home/)
- Website: [simmate.org](https://simmate.org/)
- Paper: [doi.org/10.21105/joss.04364](https://doi.org/10.21105/joss.04364)

## About

Simmate is a full-stack framework and ecosystem for chemistry research. It standardizes how researchers interact with dozens of popular tools and databases by providing a robust ORM, workflow library, and a web UI out of the box. For both molecular and crystalline systems, Simmate also provides a comprehensive toolbox to build your own custom chemistry applications.

[A preview of features is available on our documentation homepage.](https://jacksund.github.io/simmate/home/)

## Installation

The quickest way to install is with our one-line installer, which sets up [uv](https://docs.astral.sh/uv/) and the `simmate` command (including all optional app dependencies):
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

## Need help?

Post your questions and feedback [in our discussion section](https://github.com/jacksund/simmate/discussions/categories/q-a). 
