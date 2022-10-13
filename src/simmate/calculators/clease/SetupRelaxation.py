#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 12 13:09:19 2022

@author: WarrenLab
"""


from pathlib import Path

from simmate.workflow_engine import Workflow
from simmate.toolkit import Structure
from cluster_expansion import staged

class ClusterExpansion__Python__SetupRelaxation(Workflow):
    use_database = False

    @staticmethod
    def run_config(directory, **kwargs):
        working_directory = Path.cwd()

        submitted_states = []  # store the results in case you want them later
        for file in working_directory.iterdir():
            if file.suffix == ".cif":
                cif_structure = Structure.from_file(file)

                state = staged.ClusterExpansion__Vasp__Staged.run_cloud( #check this before running
                    structure=cif_structure,
                    # this names the new folder after the original cif filename
                    directory=directory / file.stem,
                    command="mpirun -n 28 vasp_std > vasp.out",
                )
                submitted_states.append(state)
                
        # ---------------------------------------------
        # Everything below is optional and only if you want to wait for and
        # the workup the results
        # ---------------------------------------------

        # wait for all runs to finish and load the results
        results = [s.result() for s in submitted_states]

        # results is a list of database objects. If you want pymatgen structures
        # again, just convert them to toolkits
        relaxed_structures = [r.to_toolkit() for r in results]

        # do whatever workup you'd like
        for relaxed_structure in relaxed_structures:
            print()
