# -*- coding: utf-8 -*-

from prefect import task

from pymatgen.core.structure import Structure


@task
def load_structure(structure):

    # How the structure was submitted as a parameter often depends on if we
    # are submitting to Prefect Cloud or running the flow locally. Therefore,
    # the structure parameter could be a number of formats. Here, we use a
    # task to convert the input to a pymatgen structure

    # if the input is already a pymatgen structure, just return it back
    if type(structure) == Structure:
        return structure
    # otherwise load the structure from the dictionary and return it
    else:
        return Structure.from_dict(structure)
