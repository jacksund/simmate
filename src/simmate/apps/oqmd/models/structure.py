# -*- coding: utf-8 -*-

from pathlib import Path

import pandas
from rich.progress import track

from simmate.database.base_data_types import Structure, table_column
from simmate.toolkit import Structure as ToolkitStructure


class OqmdStructure(Structure):
    """
    Crystal structures from the [OQMD](http://oqmd.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but OQDMD has much more data available via their
    [REST API](http://oqmd.org/static/docs/restful.html) and website.
    """

    class Meta:
        db_table = "oqmd__structures"

    # -------------------------------------------------------------------------

    html_display_name = "OQMD"
    html_description_short = "The Open Quantum Materials Database"

    html_entries_template = "oqmd/structures/table.html"
    html_entry_template = "oqmd/structures/view.html"

    # -------------------------------------------------------------------------

    external_website = "https://oqmd.org/"
    source_doi = "https://doi.org/10.1007/s11837-013-0755-4"
    is_redistribution_allowed = True

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

    remote_archive_link = "https://archives.simmate.org/OqmdStructure-2023-07-21.zip"
    archive_fields = ["formation_energy"]

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "oqmd-12345")
    """

    # OQMD did not provide energy so the Thermodynamics mix-in can't be used
    formation_energy = table_column.FloatField(blank=True, null=True)
    """
    The formation energy of the structure as provided by the OQMD.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(
        cls,
        base_directory: str = "oqmd",
        only_add_new_cifs: bool = True,
    ):
        """
        Loads OQMD data into the Simmate database.

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

        Note: there is a REST API and a python wrapper for that API (qmpy-rester),
        but the API is not good for bulk downloads and the wrapper has not been
        updated since 2021. Maybe I'll revisit their API in the future.
            - http://oqmd.org/static/docs/restful.html
            - https://github.com/mohanliu/qmpy_rester
        """

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
