# Documentation

This directory hosts the source files for Simmate's online documentation. You can access the live docs [here](https://jacksund.github.io/simmate/home/). The site is built with [Zensical](https://zensical.org/) and configured in `zensical.toml` at the root of the repo.

To preview the docs locally (with live reload), run the following after doing a dev install of Simmate:

``` bash
simmate dev docs
```

Then open [http://localhost:8000](http://localhost:8000). If you would rather have offline files, run `zensical build` and open the generated `site/` folder.
