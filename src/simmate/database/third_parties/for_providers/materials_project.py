# -*- coding: utf-8 -*-

"""

> :warning: This file is only for use by the Simmate team. Users should instead
access data via the load_remote_archive method.

This file is for pulling Materials Project data into the Simmate database. 
PyMatGen offers an easy way to do this in python -- the MPRester class. All you
need is [an API key from their site](https://materialsproject.org/open) and pymatgen
installed. For now, we only pull the mp-id, structure, and final energy.

"""

from django.db import transaction
from rich.progress import track

from simmate.database.third_parties import MatprojStructure


@transaction.atomic
def load_all_structures(
    api_key: str,
    update_stabilities: bool = False,
):
    """
    Only use this function if you are part of the Simmate dev team!

    Loads all structures directly for the Material Project database into the
    local Simmate database.

    #### Parameters

    - `api_key`:
        Your Materials Project API key.
    - `criteria`:
        Filtering criteria for which structures to load. The default is all
        existing structures (137,885 as of 2022-01-16), which will take rouhghly
        15 min to complete (not including stabilities).
    - `update_stabilities`:
        Whether to run update_all_stabilities on the database table. Note this
        will add over an hour to this process. Default is True.
    """

    try:
        from mp_api.client import MPRester
    except:
        raise Exception(
            "To use this method, MP-API is required. Please install it "
            "with `pip install mp-api"
        )

    # Connect to their database with personal API key
    with MPRester(api_key) as mpr:

        # For the filtered structures, this lists off which properties to grab.
        # All possible properties can be listed with:
        #   mpr.summary.available_fields
        fields_to_load = [
            # "builder_meta",
            # "nsites",
            # "elements",
            # "nelements",
            # "composition",
            # "composition_reduced",
            # "formula_pretty",
            # "formula_anonymous",
            # "chemsys",
            # "volume",
            # "density",
            # "density_atomic",
            # "symmetry",
            # "property_name",
            "material_id",
            # "deprecated",
            # "deprecation_reasons",
            "last_updated",
            # "origins",
            # "warnings",
            "structure",
            # "task_ids",
            "uncorrected_energy_per_atom",
            "energy_per_atom",
            # "formation_energy_per_atom",
            # "energy_above_hull",
            # "is_stable",
            # "equilibrium_reaction_energy_per_atom",
            # "decomposes_to",
            # "xas",
            # "grain_boundaries",
            "band_gap",
            # "cbm",
            # "vbm",
            # "efermi",
            "is_gap_direct",
            # "is_metal",
            # "es_source_calc_id",
            # "bandstructure",
            # "dos",
            # "dos_energy_up",
            # "dos_energy_down",
            "is_magnetic",
            # "ordering",
            "total_magnetization",
            # "total_magnetization_normalized_vol",
            # "total_magnetization_normalized_formula_units",
            # "num_magnetic_sites",
            # "num_unique_magnetic_sites",
            # "types_of_magnetic_species",
            # "k_voigt",
            # "k_reuss",
            # "k_vrh",
            # "g_voigt",
            # "g_reuss",
            # "g_vrh",
            # "universal_anisotropy",
            # "homogeneous_poisson",
            # "e_total",
            # "e_ionic",
            # "e_electronic",
            # "n",
            # "e_ij_max",
            # "weighted_surface_energy_EV_PER_ANG2",
            # "weighted_surface_energy",
            # "weighted_work_function",
            # "surface_anisotropy",
            # "shape_factor",
            # "has_reconstructed",
            # "possible_species",
            # "has_props",
            "theoretical",
        ]

        # now make the query and grab everything from the Materials Project!
        # the output dictionary is given back within a list, where each entry is
        # a specific structure (so a single mp-id)
        # Note: this is a very large query, so make sure your computer has enough
        # memory (RAM >10GB) and a stable internet connection.
        # data = mpr.summary.search(
        #     all_fields=False,
        #     fields=fields_to_load,
        #     deprecated=False,
        #     # !!! DEV NOTE: you can uncomment these lines for quick testing
        #     # num_chunks=3,
        #     chunk_size=100,
        # )

        # BUG: The search above is super unstable, so instead, I grab all mp-id
        # in one search, then make individual queries for the data of each
        # after that.
        # This takes about 30 minutes.
        mp_ids = mpr.summary.search(
            all_fields=False,
            fields=["material_id"],
            deprecated=False,
        )
        data = []
        for entry in track(mp_ids):
            result = mpr.summary.search(
                material_ids=[entry.material_id],
                all_fields=False,
                fields=fields_to_load,
            )
            data.append(result[0])

    # return data

    # Let's iterate through each structure and save it to the database
    # This also takes a while, so we use a progress bar
    failed_entries = []
    for entry in track(data):
        try:
            # convert the data to a Simmate database object
            structure_db = MatprojStructure.from_toolkit(
                id=str(entry.material_id),
                structure=entry.structure,
                energy=entry.energy_per_atom * entry.structure.num_sites,
                energy_uncorrected=entry.uncorrected_energy_per_atom
                * entry.structure.num_sites,
                updated_at=fix_timezone(entry.last_updated),
                band_gap=entry.band_gap,
                is_gap_direct=entry.is_gap_direct,
                is_magnetic=entry.is_magnetic,
                total_magnetization=entry.total_magnetization,
                is_theoretical=entry.theoretical,
            )

            # and save it to our database!
            structure_db.save()
        except:
            failed_entries.append(entry)

    return failed_entries

    # # once all structures are saved, let's update the Thermodynamic columns
    # if update_stabilities:
    #     MatprojStructure.update_all_stabilities()


# This fix function below is a copy/paste from...
#   https://stackoverflow.com/questions/18622007/

from django.conf import settings
from django.utils.timezone import make_aware


def fix_timezone(naive_datetime):

    settings.TIME_ZONE  # 'UTC'
    aware_datetime = make_aware(naive_datetime)
    aware_datetime.tzinfo  # <UTC>

    return aware_datetime
