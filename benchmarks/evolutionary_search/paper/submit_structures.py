# -*- coding: utf-8 -*-
"""
Convenience script to submit test structures for benchmarking
"""

import pandas as pd
from simmate.apps.evolution.workflows import StructurePrediction__Toolkit__FixedComposition


###############################################################################
# Load formulas from .csv file
###############################################################################
structure_df = pd.read_csv("CSPBenchmark_test_data.csv")
formulas = structure_df["full_formula"]

###############################################################################
# Submit fixed composition searches to the cloud
###############################################################################
# reset database between each search attempt
# FixedCompositionSearch.objects.all().delete()
# StaticEnergy.objects.all().delete()
# FingerprintPool.objects.all().delete()
# Relaxation.objects.all().delete()
for formula in formulas:
    print(formula)
    state = StructurePrediction__Toolkit__FixedComposition.run_cloud(
        composition = formula,
        directory = formula,
        subworkflow_name = "staged-calculation.vasp.low-quality",
        subworkflow_kwargs = dict(
            command = "mpirun -n 4 vasp_std > vasp.out", 
            compress_output = True
          ),
        nfirst_generation = 3,
        nsteadystate = 200,
        best_survival_cutoff = 10000,
        max_structures = 50000,
        min_structures_exact = 5000,
        singleshot_sources = [], # remove third party sources to avoid unfair advantage
        )
    # we don't want multiple searches using our resources at once so we wait
    # for the calculation to finish before submitting the next one
    result = state.result()

# EXAMPLE COMMAND FOR STARTING WORKERS
# simmate engine start-cluster 100 --type slurm