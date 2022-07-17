# -*- coding: utf-8 -*-

"""
This file establishes the info needed for installing your project via pip. This
then let's you import your code! For example, you can do...

``` python
from example_app.apps import ExampleAppConfig
```
    
As your project grows, you may want to update the requirements for it or even
upload it to PyPI, which let's other people download and install your code. 
To see how this setup.py file can grow, you can take a look at other example files:
    Simmate's setup.py is at... https://github.com/jacksund/simmate/blob/main/setup.py
    Another example one is at... https://github.com/pypa/sampleproject

"""

from setuptools import setup, find_packages

setup(
    name="{{ project_name }}",
    version="0.0.0",
    python_requires=">=3.10, <4",
    packages=find_packages(where="."),
    install_requires=["simmate"],
)
