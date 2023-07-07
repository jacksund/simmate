# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, Thermodynamics, table_column


class MatprojStructure(Structure, Thermodynamics):
    """
    Crystal structures from the [Materials Project](https://materialsproject.org/)
    database.

    Currently, this table only stores strucure and thermodynamic information,
    but the Materials Project has much more data available via their
    [REST API](https://github.com/materialsproject/api) and website.
    """

    class Meta:
        app_label = "data_explorer"

    archive_fields = [
        "energy_uncorrected",
        "band_gap",
        "is_gap_direct",
        "is_magnetic",
        "total_magnetization",
        "is_theoretical",
    ]
    api_filters = dict(
        energy_uncorrected=["range"],
        band_gap=["range"],
        is_gap_direct=["exact"],
        is_magnetic=["exact"],
        total_magnetization=["range"],
        is_theoretical=["exact"],
    )
    source = "Materials Project"
    source_long = "The Materials Project at Berkeley National Labs"
    homepage = "https://materialsproject.org/"
    source_doi = "https://doi.org/10.1063/1.4812323"
    remote_archive_link = "https://archives.simmate.org/MatprojStructure-2023-07-07.zip"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "mp-12345")
    """

    energy_uncorrected = table_column.FloatField(blank=True, null=True)
    """
    The reported energy of the system BEFORE Materials Project applies
    their composition-based corrections.
    """

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    """
    Whether the band gap is direct or indirect.
    """

    is_magnetic = table_column.BooleanField(blank=True, null=True)
    """
    Whether the material is magnetic
    """

    total_magnetization = table_column.FloatField(blank=True, null=True)
    """
    The total magnetization of the material
    """

    is_theoretical = table_column.BooleanField(blank=True, null=True)
    """
    Whether the material is from a theoretical structure. False indicates
    that it is experimentally known.
    """

    updated_at = table_column.DateTimeField(blank=True, null=True)
    """
    Timestamp of when this row was was lasted changed / updated by the 
    Materials Project
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the Materials Project website.
        """
        # All Materials Project structures have their data mapped to a URL in
        # the same way. For example...
        #   https://materialsproject.org/materials/mp-12345/
        return f"https://materialsproject.org/materials/{self.id}/"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_all_structures(
        cls,
        api_key: str,
        update_stabilities: bool = False,
    ):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        This method is for pulling Materials Project data into the Simmate database.


        PyMatGen offers an easy way to do this in python -- the MPRester class.
        All you need is [an API key from their site](https://materialsproject.org/open)
        and pymatgen installed.

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

        from django.utils.timezone import make_aware
        from rich.progress import track

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
            data = mpr.summary.search(
                all_fields=False,
                fields=fields_to_load,
                deprecated=False,
                # !!! DEV NOTE: you can uncomment these lines for quick testing
                # num_chunks=3,
                chunk_size=1000,
            )

            # BUG: The search above is super unstable, so instead, I grab all mp-id
            # in one search, then make individual queries for the data of each
            # after that.
            # This takes about 30 minutes.
            # mp_ids = mpr.summary.search(
            #     all_fields=False,
            #     fields=["material_id"],
            #     deprecated=False,
            # )
            # data = []
            # chunk_ids = []
            # for entry in track(mp_ids):
            #     chunk_ids.append(entry.material_id)
            #     if (
            #         len(chunk_ids) >= 1000
            #         or entry.material_id == mp_ids[-1].material_id
            #     ):
            #         result = mpr.summary.search(
            #             material_ids=[entry.material_id],
            #             all_fields=False,
            #             fields=fields_to_load,
            #         )
            #         data += result
            #         chunk_ids = []

        # Let's iterate through each structure and save it to the database
        # This also takes a while, so we use a progress bar
        failed_entries = []
        db_objects = []
        for entry in track(data):
            try:
                # convert the data to a Simmate database object
                structure_db = cls.from_toolkit(
                    id=str(entry.material_id),
                    structure=entry.structure,
                    energy=entry.energy_per_atom * entry.structure.num_sites,
                    energy_uncorrected=entry.uncorrected_energy_per_atom
                    * entry.structure.num_sites,
                    updated_at=make_aware(entry.last_updated),
                    band_gap=entry.band_gap,
                    is_gap_direct=entry.is_gap_direct,
                    is_magnetic=entry.is_magnetic,
                    total_magnetization=entry.total_magnetization,
                    is_theoretical=entry.theoretical,
                )
                db_objects.append(structure_db)
            except:
                failed_entries.append(entry)

        # and save it to our database
        cls.objects.bulk_create(
            db_objects,
            batch_size=15000,
            ignore_conflicts=True,
        )

        # once all structures are saved, let's update the Thermodynamic columns
        if update_stabilities:
            cls.update_all_stabilities()

        return failed_entries
