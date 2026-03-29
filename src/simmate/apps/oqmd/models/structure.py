# -*- coding: utf-8 -*-

import shutil
import zipfile
from pathlib import Path

import pandas
from rich.progress import track

from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import Structure, ThirdPartyData
from simmate.toolkit import Structure as ToolkitStructure


class OqmdStructure(ThirdPartyData, Structure):
    """
    Crystal structures from the [OQMD](http://oqmd.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but OQDMD has much more data available via their
    [REST API](http://oqmd.org/static/docs/restful.html) and website.
    """

    class Meta:
        db_table = "oqmd__structures"

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
        return f"http://oqmd.org/materials/entry/{self.id}"

    # -------------------------------------------------------------------------

    remote_archive_link = "https://archives.simmate.org/OqmdStructure-2026-03-29.zip"
    archive_fields = ["formation_energy"]

    # -------------------------------------------------------------------------

    energy_per_atom = table_column.FloatField(blank=True, null=True)
    """
    The final energy per atom of the structure as provided by the OQMD.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(
        cls,
        base_directory: str = None,
        only_add_new_cifs: bool = True,
    ):
        """
        Loads OQMD data into the Simmate database.

        Yichen Li was kind enough to provide all the crystal structures from
        the OQMD as POSCAR files on 2026-03-27. This makes loading the structures
        into the Simmate database much faster as we are no longer bottlenecked by
        the REST API and internet connections. (Previously Jiahong Shen provided
        these on 2022-02-21). Chris Wolverton (the PI) directed us to these students
        to help each time.

        All structures are provided as CONTCARs in a compressed folder
        (`static_contcars_all_parts.tar.gz`) containing zip files of the structures.
        There is also an excel file `oqmd_static_final_energy.xlsx` that contains
        additional data such as the final energy.

        There are currently over 1,000,000 structures and this function takes
        a few hours to run.

        Note: there is a REST API and a python wrapper for that API (qmpy-rester),
        but the API is not good for bulk downloads and the wrapper has not been
        updated since 2021. Maybe I'll revisit their API in the future.
            - http://oqmd.org/static/docs/restful.html
            - https://github.com/mohanliu/qmpy_rester
        """
        if base_directory is None:
            base_directory = (
                settings.config_directory / "oqmd" / "2026_03_27__yichen_li"
            )
        else:
            base_directory = Path(base_directory)

        # load the excel file that contains the list of ids and their energy
        df = pandas.read_csv(base_directory / "oqmd_static_final_energy.csv")
        energy_dict = dict(zip(df["oqmd_id"], df["final_energy"]))

        # Check if there are existing objects in the table to allow continuing
        # from a paused or interrupted load.
        max_id = 0
        if cls.objects.exists():
            max_id = cls.objects.order_by("-id").values_list("id", flat=True).first()

        # Handle the structure archive
        tar_path = base_directory / "static_contcars_all_parts.tar.gz"

        # We check for zip files to see if the archive has already been unpacked
        zip_files = list(base_directory.glob("*.zip"))

        if not zip_files:
            shutil.unpack_archive(tar_path, base_directory)
            zip_files = list(base_directory.glob("*.zip"))
        # iterate through the list and load the structures to our database!
        # Use rich to monitor progress.
        failed_entries = []
        db_objects = []

        for zip_path in track(zip_files, description="Processing zip files..."):
            with zipfile.ZipFile(zip_path) as z:
                for file_info in z.infolist():
                    if file_info.is_dir() or "CONTCAR" not in file_info.filename:
                        continue

                    # Filename example: oqmd_1605_calc_1228803_CONTCAR
                    name = file_info.filename.split("/")[-1]
                    parts = name.split("_")
                    if len(parts) >= 2 and parts[0] == "oqmd":
                        try:
                            entry_id = int(parts[1])
                        except ValueError:
                            continue
                    else:
                        continue

                    # Skip if we already loaded this structure in a previous run
                    if entry_id <= max_id:
                        continue

                    # load the structure from the poscar file
                    with z.open(file_info) as f:
                        contents = f.read().decode("utf-8")

                    energy = energy_dict.get(entry_id)

                    try:
                        structure = ToolkitStructure.from_str(contents, "poscar")
                        structure_db = cls.from_toolkit(
                            id=entry_id,
                            structure=structure,
                            energy_per_atom=energy,
                        )
                    except Exception:
                        structure_db = cls.from_toolkit(
                            id=entry_id,
                            structure=None,
                            energy_per_atom=energy,
                            is_invalid_structure=True,
                        )
                        failed_entries.append(entry_id)

                    db_objects.append(structure_db)

                    # save every time we have 1000 structures
                    if len(db_objects) >= 1000:
                        cls.objects.bulk_create(
                            db_objects,
                            batch_size=1000,
                            ignore_conflicts=True,
                        )
                        db_objects = []  # reset for next batch

        # and save remaining structures to our database
        if db_objects:
            cls.objects.bulk_create(
                db_objects,
                batch_size=1000,
                ignore_conflicts=True,
            )

        return failed_entries
