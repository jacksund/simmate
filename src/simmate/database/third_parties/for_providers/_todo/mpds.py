# -*- coding: utf-8 -*-

"""

This file is for pulling MPDS data into the Simmate database. 

MPDS provides a python package to make downloading their data very easy. This 
officially supported and maintained at https://github.com/mpds-io/mpds_client.
For now the package is only available via a pip install. And to help with using
this package, you should read through their guide and examples here:    
https://mpds.io/developer/#Client-library

NOTE: I'm currently running into permission issues with MPDS, and will return to
this provider after talking with their team.

"""

from django.db import transaction

from tqdm import tqdm
from simmate.toolkit import Structure
from mpds_client import MPDSDataRetrieval, MPDSDataTypes

from simmate.database import connect

from simmate.database.third_parties.mpds import MpdsStructure


@transaction.atomic
def load_all_structures(api_key="9WPgw8xYqYcB91ylff1CogIaXd4MGq6RoEZjwC1L0fh66uMw"):

    # !!! Remove key in production

    # connect to the database
    client = MPDSDataRetrieval(api_key)

    # By default, only structures from peer-reviewed papers are shown, but we
    # can switch this to include MPDS's in-house machine learning and first
    # principles structures too.
    # !!! only the ab initio and machine learning datasets are free and open
    # so I have to limit myself to those for now.
    #   client.dtype = MPDSDataTypes.ALL
    client.dtype = MPDSDataTypes.AB_INITIO

    # get_data returns a list, while get_dataframe will give us a pandas dataframe
    # I just use a list for now.
    # !!! This doesn't behave the way they claim... it definitely doesn't return
    # JSON. I'm also only ever getting hits for P-type ids (properties), when I
    # want S-type (structures)
    data = client.get_data(
        search={
            "elements": "Al-N",  # !!! for testing
            # "props": "atomic structure",
        },
        # fields={
        #     "S": [
        #         # "phase_id",
        #         # "entry",
        #         'chemical_formula',
        #         # "cell_abc",
        #         # "sg_n",
        #         # "basis_noneq",
        #         # "els_noneq",
        #     ]
        # },
    )
