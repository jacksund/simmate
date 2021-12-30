# -*- coding: utf-8 -*-

"""
This file establishes the info needed to install simmate via pip and also how to
upload it to PyPI. This file was copied and editted from the following source:
    https://github.com/pypa/sampleproject
"""

import os
from glob import glob
from setuptools import setup, find_packages
import pathlib

# Grab the full path to this file
here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")


def get_package_data(base_dir):
    """
    This function goes through the src/simmate directory and grabs all of our
    non-python files (md, rst, json, csv, yaml, html). It returns a list of
    paths to these files with the relative path starting from src/simmate.

    These should all be passed to package_data to ensure these files are
    included when simmate is installed.
    """
    # convert PosixPath to string
    base_dir = str(base_dir)

    # all designate the path to source code
    source_dir = os.path.join("src", "simmate")

    queries = [
        "**/*.md",
        "**/*.rst",
        "**/*.json",
        "**/*.csv",
        "**/*.yaml",
        "**/*.html",
    ]
    # add the base directory to the start of each query
    # we also add the source directory
    queries = [os.path.join(base_dir, source_dir, q) for q in queries]

    # now grab all the files
    all_files = []
    for query in queries:
        files = glob(query, recursive=True)
        all_files += files

    # each filename will still start with base_dir, which we want to remove.
    all_files = [os.path.relpath(f, start=source_dir) for f in all_files]

    return all_files


# For debugging get_package_data
# raise Exception(get_package_data(here))

setup(
    # published name for pip install to use
    name="simmate",
    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    version="0.0.0.dev10",
    # a quick summary and then README
    description="Simmate is a toolbox for computational materials research.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Link to our homepage. Use github for now.
    url="https://github.com/jacksund/simmate",
    # Lead dev info
    author="Jack D. Sundberg",
    author_email="jacksund@live.unc.edu",
    # Classifiers help users find your project by categorizing it.
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
    ],
    # Keywords
    keywords="sample, setuptools, development",
    # Indicate which directory the source coude is in
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # Specify which Python versions supported.
    python_requires=">=3.7",
    # This field lists other packages that your project depends on to run.
    install_requires=[
        # Core dependencies
        "numpy>=1.21.4",
        "pandas>=1.3.5",
        "django>=3.2.10",
        "prefect>=0.15.11",
        "dask>=2021.12.0",
        "click>=8.0.3",
        "numba>=0.53.0",
        # Extra (smaller) dependencies & utilities
        "django-crispy-forms>=1.13.0",  # for formatting of online forms
        "django-pandas>=0.6.1",  # for converting QuerySets to PandasDataFrames
        "dask-jobqueue>=0.7.3",  # for submitting on clusters
        "dj-database-url>=0.5.0",  # for DigitalOcean URL conversion
        "djangorestframework>=3.13.1",  # for our REST API
        "django-filter>=21.1",  # sets up automatic filters for our REST API
        "django-extensions>=3.1.5",  # simple tools to help with django development
        "pyyaml>=6.0",  # for yaml configuration files
        "plotly>=5.4.0",  # for interactive plots and visualization
        "tqdm>=4.62.3",  # for monitoring progress of long for-loops
        #
        # For development and testing
        "pytest>=6.2.5",
        "black>=21.12b0",
        #
        # These are from the MP stack and I want to phase them out over time
        "pymatgen>=2022.0.16",
        "pymatgen-analysis-diffusion>=2021.4.29",  # pymatgen-diffusion on conda
        "matminer>=0.7.4",
        # BUG: matminer's conda install is broken at the moment so we need to
        # add this dependency on our own.
        "jsonschema>=4.2.1",
        #
        # These are packages that I commonly use alongside simmate. I plan to
        # organize these into optional dependencies and/or documentation. But until
        # then, I keep them here for my own reference.
        # "psycopg2-binary>=2.9.2",  # for Postgres connections (added -binary to fix bug)
        # 'selenium',  # for web scraping (slow but robust)
        # 'spyder',  # IDE for writing/editting
        # 'gunicorn',  # for website server (Django+DigitalOcean) # !!! NOT WINDOWS
        # "graphviz==1.7",  # python-graphviz on conda. for viewing prefect flows
        # "pygraphviz==0.19",  # pygraphviz on conda. for viewing django tables
        # "scikit-learn>=1.0.1",  # for machine-learning
    ],
    # Register command line interface
    entry_points={
        "console_scripts": [
            "simmate = simmate.command_line.base_command:simmate",
        ],
    },
    # All files that aren't *.py need to be defined explicitly. Don't "automate"
    # this to grab all files because this could break installation. This can
    # be effectively the opposite of .gitignore.
    include_package_data=True,
    package_data={
        # Recursive calls are not supported yet, so keep an eye on this issue
        # https://github.com/pypa/setuptools/issues/1806
        # "simmate": [
        #     "**/*.md",
        #     "**/*.rst",
        #     "**/*.json",
        #     "**/*.csv",
        #     "**/*.yaml",
        #     "**/*.html",
        # ],
        # For now, I make a custom function that calls glob recursively
        "simmate": get_package_data(here),
    },
)
