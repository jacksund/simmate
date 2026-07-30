# -*- coding: utf-8 -*-

import logging
import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas
from rich.progress import track

from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import Structure, ThirdPartyData
from simmate.database.utils import batch_bulk_create
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

    remote_archive_link = "https://assets.simmate.org/OqmdStructure-2026-03-29.zip"
    archive_fields = ["formation_energy"]

    # -------------------------------------------------------------------------

    energy_per_atom = table_column.FloatField(blank=True, null=True)
    """
    The final energy per atom of the structure as provided by the OQMD.
    """

    # -------------------------------------------------------------------------

    @classmethod
    @batch_bulk_create(batch_size=1_000)
    def load_source_data(
        cls,
        base_directory: str = None,
        only_add_new_cifs: bool = True,
    ):
        """
        Downloads and loads OQMD data into the Simmate database.

        Source files are downloaded from `https://assets.simmate.org/oqmd/raw/`
        if they are not already present in the base directory.

        Yichen Li was kind enough to provide all the crystal structures from
        the OQMD as POSCAR files on 2026-03-24. This makes loading the structures
        into the Simmate database much faster as we are no longer bottlenecked by
        the REST API and internet connections. (Previously Jiahong Shen provided
        these on 2022-02-21). Chris Wolverton (the PI) directed us to these students
        to help each time.

        All structures are provided as CONTCARs in a compressed folder
        (`static_contcars_all_parts.tar.gz`) containing zip files of the structures.
        There is also a csv file `static_final_energy.csv` that contains
        additional data such as the final energy. We host these files on Cloudflare
        R2 for easy access by others.

        There are currently over 1,000,000 structures and this function takes
        a few hours to run.
        """
        base_directory = Path(
            base_directory or settings.config_directory / "oqmd" / "raw"
        )
        base_directory.mkdir(parents=True, exist_ok=True)

        # Download files if they do not exist
        files = {
            "static_contcars_all_parts-2026-03-24.tar.gz": None,
            "static_final_energy-2026-03-24.csv": None,
        }
        for filename in files:
            file_path = base_directory / filename
            files[filename] = file_path
            if not file_path.exists():
                logging.info(f"Downloading {filename}...")
                url = f"https://assets.simmate.org/oqmd/raw/{filename}"
                urllib.request.urlretrieve(url, file_path)

        tar_path, csv_path = files.values()

        # load the csv file that contains the list of ids and their energy
        df = pandas.read_csv(csv_path)
        energy_dict = dict(zip(df["oqmd_id"], df["final_energy"]))

        if only_add_new_cifs:
            logging.info("Gathering existing IDs...")
            existing_ids = set(cls.objects.values_list("id", flat=True))
        else:
            existing_ids = set()

        # We check for zip files to see if the archive has already been unpacked
        zip_files = list(base_directory.glob("*.zip"))
        if not zip_files:
            shutil.unpack_archive(tar_path, base_directory)
            zip_files = list(base_directory.glob("*.zip"))

        # iterate through the list and load the structures to our database!
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
                    if entry_id in existing_ids:
                        continue

                    # load the structure from the poscar file
                    with z.open(file_info) as f:
                        contents = f.read().decode("utf-8")

                    energy = energy_dict.get(entry_id)

                    try:
                        structure = ToolkitStructure.from_str(contents, "poscar")
                        # Mark overly complex structures as invalid to avoid database blowup
                        if len(structure) > 500 or len(structure.composition) > 10:
                            raise ValueError("Structure too complex")
                        yield cls.from_toolkit(
                            id=entry_id,
                            structure=structure,
                            energy_per_atom=energy,
                        )
                    except Exception:
                        yield cls.from_toolkit(
                            id=entry_id,
                            structure=None,
                            energy_per_atom=energy,
                            is_invalid_structure=True,
                        )
