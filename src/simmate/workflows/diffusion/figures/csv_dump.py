# -*- coding: utf-8 -*-

from simmate.shortcuts import setup
from simmate.database.diffusion import Pathway as Pathway_DB


queryset = (
    Pathway_DB.objects.filter(vaspcalca__isnull=False)
    .select_related("vaspcalca", "empiricalmeasures", "structure")
    .all()
)
# .to_pymatgen().write_path("test.cif", nimages=3)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "length",
        "atomic_fraction",
        "structure__id",
        "structure__nsites",
        "structure__nelement",
        "structure__chemical_system",
        "structure__density",
        "structure__spacegroup",
        "structure__formula_full",
        "structure__formula_reduced",
        "structure__formula_anonymous",
        "structure__final_energy",
        "structure__final_energy_per_atom",
        "structure__formation_energy_per_atom",
        "structure__e_above_hull",
        # "empiricalmeasures__oxidation_state",
        "empiricalmeasures__dimensionality",
        "empiricalmeasures__dimensionality_cumlengths",
        "empiricalmeasures__ewald_energy",
        "empiricalmeasures__ionic_radii_overlap_cations",
        "empiricalmeasures__ionic_radii_overlap_anions",
        "vaspcalca__energy_start",
        "vaspcalca__energy_midpoint",
        "vaspcalca__energy_end",
        "vaspcalca__energy_barrier",
        # "nsites_101010",
        # "vaspcalcb__energy_barrier",
    ],
)
