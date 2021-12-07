# -*- coding: utf-8 -*-

import os

INSTALLATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

with open(
    os.path.join(INSTALLATION_DIRECTORY, "README.rst"), encoding="utf-8"
) as docs_file:
    __doc__ = docs_file.read()
