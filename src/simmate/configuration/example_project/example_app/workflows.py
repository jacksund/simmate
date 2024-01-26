# -*- coding: utf-8 -*-

"""
Building a workflow in Simmate can sometimes involve using custom database
tables, so before you start editting this file, make sure you have gone through
and editted the `models.py` file.

Below is an example of a simple VaspWorkflow, which is used to run a single VASP
calculation.

As your need grow, you may need more complex Workflows. For complex workflows that
require several calculations, other python logic, and parallelization, make
sure you read through the documentation for 
[the Workflow class](https://jacksund.github.io/simmate/full_guides/workflows/overview/) 
as well as relevent subclasses like the
[S3Workflow](https://jacksund.github.io/simmate/full_guides/workflows/s3_workflows/)
or 
[VaspWorkflow](https://jacksund.github.io/simmate/full_guides/workflows/third_party_software/vasp/overview/)
"""

from simmate.engine import Workflow, workflow
from simmate.toolkit import Structure

# Import our tables from the other files.
from .models import MyCustomTable2

# -----------------------------------------------------------------------------
# Make sure to list out all workflows that you want registered
# -----------------------------------------------------------------------------

__all__ = [
    "add",
    "Example__Python__MyExample",
]

# -----------------------------------------------------------------------------
# Our first example shows off the basics
# -----------------------------------------------------------------------------


@workflow
def add(x, y, **kwargs):
    """
    A basic workflow that adds two numbers together
    """
    return x + y


class Example__Python__MyExample(Workflow):
    """
    A basic workflow that returns a dictionary, which then updates a database table.

    Once ran, note how the structure and inputs are saved at the start of the
    calculation. Plus the outputs are saved once it finishes
    """

    database_table = MyCustomTable2  # tells the workflow to use this table

    @staticmethod
    def run_config(
        input_01: float,
        input_02: any,
        structure: Structure,
        **kwargs,
    ):
        # This is a boring workflow because it just saves the input values
        # to our table. You can get much more creative with workflows though
        return {
            "output_01": input_01 * 100,
            "output_02": False,
        }
