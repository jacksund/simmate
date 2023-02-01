# -*- coding: utf-8 -*-

from pymatgen.analysis.structure_matcher import StructureMatcher
from rich.progress import track

from simmate.database import connect
from simmate.database.base_data_types import FingerprintPool
from simmate.database.workflow_results import (
    ChemicalSystemSearch,
    FixedCompositionSearch,
    Relaxation,
    StaticEnergy,
)
from simmate.toolkit import Structure
from simmate.utilities import get_directory

# reset database between each search attempt
# FixedCompositionSearch.objects.all().delete()
# StaticEnergy.objects.all().delete()
# FingerprintPool.objects.all().delete()
# Relaxation.objects.all().delete()

# EXAMPLE JOB SCRIPT
# workflow_name: structure-prediction.toolkit.fixed-composition
# composition: Si4N4O2
# directory: search-output
# subworkflow_kwargs:
#   command: mpirun -n 4 vasp_std > vasp.out
#   compress_output: true
# nfirst_generation: 3
# nsteadystate: 200
# best_survival_cutoff: 10000
# max_structures: 50000
# min_structures_exact: 5000

# EXAMPLE COMMANDS FOR START SEARCH AND WORKERS
# simmate workflows run search.yaml
# simmate engine start-cluster 100 --type slurm

# -----------------------------------------------------------------------------
# Fix buggy structures
# -----------------------------------------------------------------------------

# in 2 out of the 75k+ structures of a Y-S-F search, VASP gave an excessively
# large (negative) and incorrect energy. Recalculating the structure energy
# confirmed these were incorrect. These energies throw off the hull energy
# calculations so I need to delete them

# df = (
#     Relaxation.objects.filter(
#         energy__isnull=False,
#         formula_reduced="Y4S3F2",
#         workflow_name="relaxation.vasp.staged",
#     )
#     .all()
#     .to_dataframe()
# )

# structure = Relaxation.objects.get(id=327643) # "Y2S6F"
# structure = Relaxation.objects.get(id=304806) # "Y4S3F2"
# structure.to_toolkit().to("cif", "buggy_structure.cif")
columns = [
    "id",
    "chemical_system",
    "formula_full",
    "formula_reduced",
    "energy",
    "energy_per_atom",
    "energy_above_hull",
    "formation_energy_per_atom",
    "decomposes_to",
    "band_gap",
    "directory",
    "total_time",
]
df = (
    Relaxation.objects.filter(
        workflow_name="relaxation.vasp.staged",
        energy__isnull=False,
    )
    .only(*columns)
    .to_dataframe(columns)
)

# -----------------------------------------------------------------------------
# Setup and loading (Chemical-system search)
# -----------------------------------------------------------------------------

search = ChemicalSystemSearch.objects.get(id=5)
d = get_directory("search-output")
search.write_output_summary(d)

# -----------------------------------------------------------------------------
# Setup and loading (Fixed-composition search)
# -----------------------------------------------------------------------------

search = FixedCompositionSearch.objects.get(id=4)

expected_structure = Structure.from_dynamic(
    # "benchmark_structures/SiO2-6945_opt.cif",
    # "benchmark_structures/Al2O3-1143_opt.cif",
    "benchmark_structures/Si2N2O-4497_opt.cif",
    # "benchmark_structures/MgSiO3-603930_opt.cif",
    # "benchmarks/evolutionary_search/benchmark_structures/MgSiO3-603930_opt.cif",
)

# -----------------------------------------------------------------------------
# Write outputs
# -----------------------------------------------------------------------------

d = get_directory("search-output")

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
else:
    print("Found groundstate!")

# -----------------------------------------------------------------------------
# Check for computational time
# -----------------------------------------------------------------------------

# total real time of the search
search_time = (individual.finished_at - search.started_at).total_seconds()

# total CPU time of all individuals in the search
job_time = sum(
    search.individuals_completed.filter(
        finished_at__lte=individual.finished_at
    ).values_list("total_time", flat=True)
)

# cpu time take the mpirun parallelism into account too
# we used "mpirun -n 4" for all calcs
cpu_time = job_time * 4

print(n + 1)
print(search_time)
print(job_time)
print(cpu_time)

# -----------------------------------------------------------------------------
# Check most similar
# -----------------------------------------------------------------------------

search.write_correctness_plot(directory=d, structure_known=expected_structure)

# -----------------------------------------------------------------------------
