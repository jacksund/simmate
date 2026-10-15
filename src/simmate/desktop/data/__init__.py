# -*- coding: utf-8 -*-

"""
The data behind the Toolkit tab, kept apart from Qt: reading dataset files,
working out what each column holds, and the opened dataset with its molecules.
"""

from .columns import (
    CATEGORY,
    DATE,
    MOLECULE,
    NUMBER,
    TEXT,
    DataColumns,
)
from .dataset import ToolkitDataset
from .readers import READ_SUFFIXES, read_table
