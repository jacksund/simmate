#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from simmate.engine import Workflow
from simmate.apps.warrenapp.workflows.badelf.badelf_alg_v0_4_0 import BadElfAnalysis__Warren__BadelfIonicRadii
from simmate.apps.warrenapp.badelf_tools.utilities import write_density_file_empty
from simmate.apps.warrenapp.models.badelf import BadElfAnalysis

from simmate.conftest import SimmateMockHelper, copy_test_files
from simmate.toolkit import Structure

"""
Things to test:
    1. Making empty files
    2. badelf algorithm
"""


# class Testing__BadElfDatabase__Dummy(Workflow):
#     """
#     A minimal workflow for testing if the BadELF database is functioning
#     """
#     database_table = BadElfAnalysis
#     def run_config(cls, **kwargs):
#         results_dataframe = {
#                 "oxidation_states": [1,2],
#                 "algorithm": "badelf",
#                 "charges": [1,2],
#                 "min_dists": [1,2],
#                 "atomic_volumes": [1,2],
#                 "element_list": ["Na", "Cl"],
#                 "vacuum_charge": 0,
#                 "vacuum_volume": 0,
#                 "nelectrons": 3,
#                 "nelectrides": 0, 
#             }
#         return results_dataframe
        
# def test_badelf(sample_structures, tmp_path, mocker):
#     copy_test_files(
#         tmp_path,
#         test_directory=__file__,
#         test_folder="badelf.zip",
#     )
    
#     structure = Structure.from_file(tmp_path / "POSCAR")
#     # create empty files
#     write_density_file_empty(
#         directory = tmp_path, 
#         structure = structure)
#     # assert that each empty file was created
#     empty_files = "POSCAR_empty", "ELFCAR_empty", "CHGCAR_empty"
#     for file in empty_files:
#         file_path = tmp_path / file
#         assert file_path.exists()
        
#     # Now we are going to test the badelf algorithm. Ideally we would test the
#     # zero-flux algorithm as well, but this requires that bader be installed
#     result = BadElfAnalysis__Warren__BadelfIonicRadii().run(
#         structure=structure,
#         directory=tmp_path,
#         print_atom_voxels=True,
#         ).result()
    
#     columns = ["oxidation_states",
#     "algorithm",
#     "charges",
#     "min_dists",
#     "atomic_volumes",
#     "element_list",
#     "vacuum_charge",
#     "vacuum_volume",
#     "nelectrons",
#     "nelectrides"] 
#     assert all(i in result.keys() for i in columns)
    
    