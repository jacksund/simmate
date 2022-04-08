# Documentation

This directory hosts the build script for Simmate's online API documentation. You can access the live docs [here](https://jacksund.github.io/simmate/simmate.html). If you would like to host our documentation locally for offline access, then you can run the following commands

``` bash
# with your simmate conda env active
pip install pdoc
python make_docs.py
```

You can then open up the generated `docs/index.html` file to view the offline documentation.


# Maintainer Notes

In the future, I may be able to stop tracking these html files with git (which throw our contributor page out of wack). Instead, I could consider adding the following workflow from pdoc. I tried this before, but failed to get things working:

``` yaml
# This workflow runs pdoc to automatically generate our documentation.
# This file was copied and modified from...
#   https://github.com/mitmproxy/pdoc/blob/main/.github/workflows/docs.yml
# The guide is located here...
#   https://pdoc.dev/docs/pdoc.html#deploying-to-github-pages

name: Run pdoc

# build the documentation whenever there are new commits on main
# on:
#   release:
#     types: [published]
# using on-push for testing
on:
  push:
    branches: [ main ]

# security: restrict permissions for CI jobs.
permissions:
  contents: read

jobs:
  # Build the documentation and upload the static HTML files as an artifact.
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python 3.10
        uses: actions/setup-python@v2
        with:
            python-version: "3.10"

      - name: Add conda to system path
        run: |
            # $CONDA is an environment variable pointing to the root of the miniconda directory
            echo $CONDA/bin >> $GITHUB_PATH

      - name: Install dependencies
        run: |
            conda update -n base -c defaults conda
            conda env update -f tutorials/Guides_for_contributors/environment.yaml -n base
            pip install -e .
            pip install pdoc
            # consider adding optional dependencies from third-parties module

      # BUG: This line is currently failing with permission errors. Might
      # need to use sudo or alter permissions above.
      - name: Run pdoc            
        run: docs/make_docs.py
      
      # make results accessible to github via artifacts
      - run: tar --directory docs/ -hcf artifact.tar .
      - uses: actions/upload-artifact@v3
        with:
          name: github-pages
          path: ./artifact.tar

  # Deploy the artifact to GitHub pages.
  # This is a separate job so that only actions/deploy-pages has the necessary permissions.
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v1
```
