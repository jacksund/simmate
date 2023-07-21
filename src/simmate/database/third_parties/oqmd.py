# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, table_column


class OqmdStructure(Structure):
    """
    Crystal structures from the [OQMD](http://oqmd.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but OQDMD has much more data available via their
    [REST API](http://oqmd.org/static/docs/restful.html) and website.
    """

    class Meta:
        app_label = "data_explorer"

    archive_fields = ["formation_energy"]
    api_filters = dict(formation_energy=["range"])
    source = "OQMD"
    source_long = "The Open Quantum Materials Database"
    homepage = "https://oqmd.org/"
    source_doi = "https://doi.org/10.1007/s11837-013-0755-4"
    remote_archive_link = "https://archives.simmate.org/OqmdStructure-2023-07-21.zip"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "oqmd-12345")
    """

    # OQMD did not provide energy so the Thermodynamics mix-in can't be used
    formation_energy = table_column.FloatField(blank=True, null=True)
    """
    The formation energy of the structure as provided by the OQMD.
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the OQMD website.
        """
        # Links to the OQMD dashboard for this structure. An example is...
        #   http://oqmd.org/materials/entry/10435
        id_number = self.id.split("-")[-1]  # this removes the "oqmd-" from the id
        return f"http://oqmd.org/materials/entry/{id_number}"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_all_structures_from_files(
        cls,
        base_directory: str = "oqmd",
        only_add_new_cifs: bool = True,
    ):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        This method is for pulling OQMD data into the Simmate database.

        There are many ways to pull from this database, but it looks like the easiest
        is the qmpy_rester python package. This officially supported and maintained
        at https://github.com/mohanliu/qmpy_rester. For now the package is only available
        via a pip install.

        For other options such as the REST API, check out
        http://oqmd.org/static/docs/restful.html

        # For this method specifically...

        Jiahong Shen was kind enough to provide all the crystal structures from
        the OQMD as POSCAR files. This makes loading the structures into the
        Simmate database much faster as we are no longer bottlenecked by the REST
        API and internet connections.

        All POSCARs are in the same folder, where the name of each is the
        <id>-<composition> (ex: 12345-NaCl). There are also csv's that contain
        additional data such as the energy:

            - all_oqmd_entry.csv
            - all_public_entries.csv
            - all_public_fes.csv
            - get_all_entry_id_public.py
            - get_all_entry_poscar.py

        There are currently 1,013,654 structures and this function takes roughly
        3hrs to run.
        """

        from pathlib import Path

        import pandas
        from rich.progress import track

        from simmate.toolkit import Structure as ToolkitStructure

        base_directory = Path(base_directory)

        # load the csv that contains the list of filenames and their values
        df = pandas.read_csv(base_directory / "all_oqmd_entry.csv")
        # df = df[:1000]  # FOR TESTING

        # iterate through the list and load the structures to our database!
        # Use rich to monitor progress.
        failed_entries = []
        db_objects = []
        for _, row in track(df.iterrows(), total=len(df)):
            # load the structure from the poscar file
            filename = base_directory / row.filename
            with filename.open() as file:
                contents = file.read()
            structure = ToolkitStructure.from_str(contents, "poscar")

            # save the data to the Simmate database
            # now convert the entry to a database object
            try:
                structure_db = cls.from_toolkit(
                    id="oqmd-" + str(row.entry_id),
                    structure=structure,
                    formation_energy=row.formationenergy,
                )
                db_objects.append(structure_db)
            # A few structures fail because of the symmetry analyzer can't determine
            # the spacegroup. These are...
            # 1443135, 1443014, 1451986, 1452015, 1452024
            except:
                failed_entries.append(row.entry_id)

        # and save it to our database
        cls.objects.bulk_create(
            db_objects,
            batch_size=15000,
            ignore_conflicts=True,
        )

        return failed_entries

    @classmethod
    def _load_all_structures_from_api(cls):
        """
        Only use this function if you are part of the Simmate dev team!

        Loads all structures directly for the OQMD database into the local
        Simmate database.

        THIS METHOD IS OUTDATED -- Use the _load_all_structures_from_files
        method instead
        """
        from rich.progress import track

        from simmate.toolkit import Structure as ToolkitStructure

        # OQMD is not a dependency of simmate, so make sure you install it before
        # using this method
        try:
            import qmpy_rester
        except:
            raise ModuleNotFoundError(
                "You must install qmpy-rester with `pip install qmpy_rester`"
            )
        # The documentation indicates that we handle a query via a context manager
        # for qmpy_rester. Each query is returned as a page of data, where we need
        # to iterate through all of the pages. To do this, we constantly make a query
        # and check the "next" field, which tells us if its the last page or not.

        # as we download all the data, we store it in a main list
        data = []

        # starting from the first page, assume we aren't on the last page until told
        # otherwise. And loop until we know its the last page.
        current_page = 0
        is_last_page = False
        results_per_page = 100  # based on OQMD recommendations
        while not is_last_page:
            with qmpy_rester.QMPYRester() as query:
                # make the query
                result = query.get_oqmd_phases(
                    verbose=False,
                    limit=results_per_page,
                    offset=current_page * results_per_page,
                    #
                    # Note delta_e is the formation energy and then stability is the
                    # energy above hull.
                    fields="entry_id,unit_cell,sites,delta_e",
                    # element_set="Al,C",  # Useful for testing
                )
                # grab the data for the next slice of structures
                query_slice = result["data"]
                # And check to see if this is the last page. The logic here is if
                # there is data for "next", then it isn't the last page
                is_last_page = not bool(result["links"]["next"])

                # store the slice of entrys in our main list
                for entry in query_slice:
                    data.append(entry)
                # on the very first page, let's also check the total number of pages
                if current_page == 0:
                    total_pages = result["meta"]["data_available"] // results_per_page
                # move on to the next page
                print(f"Successfully downloaded page {current_page} of {total_pages}")
                current_page += 1
        # Now iterate through all the data -- which is a list of dictionaries.
        # We convert the data into a pymatgen object and sanitize it before saving
        # to the Simmate database
        for entry in track(data):
            # Parse the data into a pymatgen object
            # Also before converting into a pymatgen object, we need to parse the sites,
            # which are given as a list of "Element @ X Y Z" (ex: "Na @ 0.5 0.5 0.5")
            # Changing this format is why we have this complex lists below
            structure = ToolkitStructure(
                lattice=entry["unit_cell"],
                species=[site.split(" @ ")[0] for site in entry["sites"]],
                coords=[
                    [float(n) for n in site.split(" @ ")[1].split()]
                    for site in entry["sites"]
                ],
                coords_are_cartesian=False,
            )

            # now convert the entry to a database object
            structure_db = cls.from_toolkit(
                id="oqmd-" + str(entry["entry_id"]),
                structure=structure,
                energy=entry["delta_e"],
            )

            # and save it to our database!
            structure_db.save()
