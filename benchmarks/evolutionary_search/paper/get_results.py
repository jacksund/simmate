# -*- coding: utf-8 -*-

from pymatgen.analysis.structure_matcher import StructureMatcher
from rich.progress import track

from simmate.database import connect
from simmate.apps.evolution.models import FixedCompositionSearch
from simmate.database.third_parties import MatprojStructure
import pandas as pd
from pathlib import Path


# get expected structures
structure_df = pd.read_csv("CSPbenchmark_test_data.csv")
###############################################################################
# Make dataframe to store results
###############################################################################
results_df = structure_df.copy()
none_list = [None for i in range(len(results_df))]
results_df["structure_found"] = none_list
results_df["real_time"] = none_list
results_df["cpu_time"] = none_list
results_df["total_structures_searched"] = none_list

# -----------------------------------------------------------------------------
# check each search
# -----------------------------------------------------------------------------
for i, row in results_df.iterrows():
    formula = row["full_formula"]
    mp_id = row["material_id"]
    search = FixedCompositionSearch.objects.filter(composition=formula)
    
    expected_structure = MatprojStructure.objects.get(id=mp_id)
    
    # -----------------------------------------------------------------------------
    # Write outputs
    # -----------------------------------------------------------------------------
    
    d = Path(search.directory)
    
    expected_structure.to("cif", d / "expected.cif")
    search.best_individual.to_toolkit().to("cif", d / "best.cif")
    search.write_output_summary(d)
    
    # -----------------------------------------------------------------------------
    # Check for exact match
    # -----------------------------------------------------------------------------
    
    individuals = search.individuals_completed.order_by("finished_at").all()
    structures = individuals.to_toolkit()
    
    matcher = StructureMatcher(attempt_supercell=True)
    
    for n, individual in track(list(enumerate(individuals))):
        structure = individual.to_toolkit()
    
        is_match = matcher.fit(expected_structure, structure)
        if is_match:  # or individual.id == 76827
            structure.to("cif", d / "match.cif")
            break
    
    if not is_match:
        print("Search has not found groundstate yet")
        results_df.loc[i,"structure_found"] = False
    else:
        print("Found groundstate!")
        results_df.loc[i,"structure_found"] = True
    
    # -----------------------------------------------------------------------------
    # Check for computational time
    # -----------------------------------------------------------------------------
    
    # total real time of the search
    search_time = (individual.finished_at - search.started_at).total_seconds()
    results_df.loc[i,"real_time"] = search_time
    # total CPU time of all individuals in the search
    job_time = sum(
        search.individuals_completed.filter(
            finished_at__lte=individual.finished_at
        ).values_list("total_time", flat=True)
    )
    # add completed structures amount
    results_df.loc[i, "total_structures_searched"] = len(search.individuals_completed)
    
    # cpu time take the mpirun parallelism into account too
    # we used "mpirun -n 4" for all calcs
    cpu_time = job_time * 4
    results_df.loc[i,"cpu_time"] = cpu_time
    print(n + 1)
    print(search_time)
    print(job_time)
    print(cpu_time)
    
    # -----------------------------------------------------------------------------
    # Check most similar
    # -----------------------------------------------------------------------------
    
    search.write_correctness_plot(directory=d, structure_known=expected_structure)
    
    # -----------------------------------------------------------------------------
results_df.to_csv("search_results.csv")