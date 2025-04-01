# -*- coding: utf-8 -*-

import gzip
import logging
import shutil
from pathlib import Path

import pandas
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.configuration import settings
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.utilities import chunk_list, get_directory


class Emolecules(Molecule):
    """
    Molecules from the [eMolecules](https://www.emolecules.com/) database.
    """

    # disable cols
    source = None

    html_display_name = "eMolecules"
    html_description_short = "A vendor catalog of chemicals"

    external_website = "https://www.emolecules.com/"
    source_doi = "https://www.emolecules.com/data-downloads"

    # emol_versions_id --> set to id in the table
    emol_parent_id = table_column.IntegerField(blank=True, null=True)

    is_active_listing = table_column.BooleanField(blank=True, null=True, default=True)
    """
    eMolecules will sometimes signal that compounds are removed -- either from
    removing problematic compounds or the suppliers no longer provide the
    product. Simmate still keeps these records in the database and removes
    the active flag.
    """

    is_building_block = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether eMolecules considers this compound a "building block". Building
    blocks are small molecules that are typically use as starting materials
    and often available for purchase. So many of these compounds will have
    `vendor_offers` associated with them.
    """

    # ----------------------------
    # These are other table headers that are only populated if the user has
    # an eMolecules subscription (via the bb metadata)
    # ----------------------------

    cas_compound = table_column.ForeignKey(
        "datasets.CasRegistry",  # str to prevent circ import
        on_delete=table_column.PROTECT,
        null=True,
        blank=True,
        related_name="+",  # disabled
    )
    """
    The CAS number associated with this compound.
    
    Note, this CAS number points to Simmate's internal CAS Registry and
    is verified against the compounds provided by eMolecules. If both a
    `cas_compound` and `cas_number_original` are available, this column should
    take priority as it has been verified.
    """

    cas_number_original = table_column.TextField(blank=True, null=True)
    """
    The associated CAS number as reported by eMolecules.
    
    This is separate from the `cas_number` column, which is a foreign key
    to the CAS Registry table within Simmate. See `cas_number` column for
    more info.
    """

    mfcd = table_column.TextField(blank=True, null=True)
    """
    The MFCD (MDL Number or Molecular Formula Chemical Directory number) is a 
    unique identifier assigned to chemical substances by the Molecular Design 
    Limited (MDL) company, now part of Elsevier.
    """

    # ----------------------------

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the eMolecules website.
        """
        return f"https://search.emolecules.com/search/#?query={self.id}&querytype=emoleculesid"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(
        cls,
        update_only: bool = True,
        building_blocks: bool = True,
        building_block_offers: bool = True,
        screening_collection: bool = True,
        custom_offers: bool = True,
    ):

        # Methods below populate the EmoleculesSupplierOffer table.
        # import here to prevent circular import
        from .supplier_offers import EmoleculesSupplierOffer

        files = cls._download_files()

        def get_file(set_type: str, filename: str):
            for file in files:
                if file.parent.parent.name == set_type and file.name == filename:
                    return file
            raise Exception(f"File not found: {set_type} / {filename}")

        if building_blocks:
            cls._load_building_blocks(
                structures_file=get_file(
                    "building_blocks",
                    "structures.sdf",
                ),
                update_only=update_only,
            )

        if building_block_offers:
            EmoleculesSupplierOffer._load_building_blocks_metadata(
                metadata_file=get_file(
                    "building_blocks",
                    "metadata.tsv",
                ),
                update_only=update_only,
            )

        if screening_collection:
            cls._load_screening_collection(
                version_smi_file=get_file(
                    "screening_collection",
                    "version.smi",
                ),
                version_deleted_file=get_file(
                    "screening_collection",
                    "version_deleted.txt",
                ),
                version_incremental_file=get_file(
                    "screening_collection",
                    "version_incremental.sdf",
                ),
                update_only=update_only,
            )

        if custom_offers:
            EmoleculesSupplierOffer._load_custom_pricestable(
                custom_file=get_file(
                    "screening_collection",
                    settings.emolecules.custom_offers,
                ),
                update_only=update_only,
            )

    @classmethod
    def _download_files(cls, unpack: bool = True, use_old: bool = True):

        # Grab eMol settings
        emol_base_url = settings.emolecules.file_server
        emol_auth = HTTPBasicAuth(
            username=settings.emolecules.user,
            password=settings.emolecules.password,
        )

        final_files = []
        download_config = [
            [
                "screening_collection",
                "/monthly_dump_sc",
                [
                    "version_deleted.txt.gz",
                    "version.smi.gz",  # unpacks to ~2.5GB
                    "version_incremental.sdf.gz",  # !!! why isnt there an incremental smi...
                ],
            ],
            [
                "building_blocks",
                "/monthly_dump_bb",
                [
                    "metadata.tsv",
                    "structures.sdf",  # ~3.5 GB
                ],
            ],
        ]
        for foldername, endpoint, files_to_download in download_config:

            # Grab the full list of dumps (which are named based on date) and
            # then use the lastest one
            url = emol_base_url + endpoint
            response = requests.get(
                url,
                auth=emol_auth,
                verify=False,
            )
            soup = BeautifulSoup(response.content, "html.parser")
            hrefs = [
                a["href"]
                for a in soup.find_all("a", href=True)
                if not a["href"].startswith("?") and not a["href"].startswith("/")
            ]
            lastest_ref = hrefs[-1]

            download_dir = get_directory(
                settings.config_directory / "emolecules" / foldername / lastest_ref
            )

            # Load data from selected ref
            for filename in files_to_download:

                download_filename = download_dir / filename

                # only download if it doesn't exist or a new copy is requested
                if not (use_old and download_filename.exists()):
                    url = emol_base_url + endpoint + "/" + lastest_ref + filename
                    response = requests.get(
                        url,
                        auth=emol_auth,
                        verify=False,
                    )
                    if response.status_code != 200:
                        raise Exception("Failed to download file")
                    with download_filename.open("wb") as file:
                        file.write(response.content)

                # Unpack .gz files if requested

                if unpack and download_filename.suffix == ".gz":
                    unpacked_filename = download_dir / download_filename.stem
                    if not (use_old and unpacked_filename.exists()):
                        with gzip.open(download_filename, "rb") as f_in:
                            with unpacked_filename.open("wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    # replace filename for final_files use
                    download_filename = unpacked_filename

                final_files.append(download_filename)

        return final_files

    @classmethod
    def _load_screening_collection(
        cls,
        version_smi_file: str | Path = "version.smi",
        version_deleted_file: str | Path = "version_deleted.txt",
        version_incremental_file: str | Path = "version_incremental.sdf",
        update_only: bool = False,
    ):

        # Load all files and metadata
        current_listing = pandas.read_csv(version_smi_file, delimiter=" ")
        all_ids = set(current_listing.version_id.to_list())

        incremental_ids = set(
            pandas.DataFrame(
                [
                    mol.metadata["EMOL_VERSION_ID"]
                    for mol in ToolkitMolecule.from_sdf_file(
                        filename=version_incremental_file,
                        skip_failed=True,
                    )
                ],
            )[0].to_list()
        )
        inactive_ids = set(
            pandas.read_csv(version_deleted_file, header=None)[0].to_list()
        )
        simmate_ids = set(cls.objects.values_list("id", flat=True).all())

        # Start by marking inactive ids. we do this in chunks so its easier on
        # the database, and only use the "deleted" file is update_only=True
        inactive_ids_to_update = []
        for emol_id in all_ids:
            if emol_id in inactive_ids:
                inactive_ids_to_update.append(emol_id)
            # only do this full check during full_sync
            elif not update_only and emol_id in simmate_ids:
                inactive_ids_to_update.append(emol_id)
        if inactive_ids_to_update:
            for id_chunk in chunk_list(
                full_list=inactive_ids_to_update, chunk_size=250
            ):
                cls.objects.filter(id__in=id_chunk).update(is_active_listing=False)

        # now we update/add the full rows

        # if we only want to update the current db, then we cut down the current
        # listing ids to only those that are *missing* from the simmate db and
        # that are in the incremental listings (which always need updated)
        if update_only:
            update_only_ids = all_ids - (simmate_ids - incremental_ids)
            current_listing = current_listing[
                current_listing.version_id.isin(update_only_ids)
            ]

        # split the ids we need to update into chunks to make things easier
        # on the database (rather than making millions of db_objs in one go)
        chunk_size = 25_000
        nchunk = 0
        nchunks_total = (len(current_listing) // chunk_size) + 1
        failed_rows = []
        for emol_chunk in chunk_list(current_listing, chunk_size):

            logging.info(f"CHUNK # {nchunk} of {nchunks_total}")
            nchunk += 1

            logging.info("Generating database objects...")
            db_objs = []
            for i, row in track(emol_chunk.iterrows(), total=len(emol_chunk)):
                try:
                    molecule = ToolkitMolecule.from_smiles(row.isosmiles)
                    molecule_db = cls.from_toolkit(
                        id=row.version_id,
                        emol_parent_id=row.parent_id,
                        molecule=molecule,
                        molecule_original=row.isosmiles,
                    )
                    db_objs.append(molecule_db)
                except:
                    failed_rows.append(row.to_dict())

            logging.info("Saving to Simmate database...")
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
                # BUG: is it possible for a structure to change...?
                # update_conflicts=True,
                # unique_fields=["id"],
                # update_fields=[...],
            )

            # logging.info("Adding molecule fingerprints...")
            # cls.populate_fingerprint_database()
            # disabled until I have enough disk space. Would take >100GB

        logging.info("Done!")
        return failed_rows

    @classmethod
    def _load_building_blocks(
        cls,
        structures_file="structures.sdf",
        update_only: bool = False,
    ):

        # Load all files and metadata
        logging.info("Loading building block data...")
        current_listing = pandas.DataFrame(
            [
                [
                    mol.metadata["SMILES"],
                    mol.metadata["Parent ID"],
                    mol.metadata["Version ID"],
                    mol.metadata.get("MFCD"),
                    mol.metadata.get("CAS"),
                ]
                for mol in ToolkitMolecule.from_sdf_file(
                    filename=structures_file,
                    skip_failed=True,
                )
            ],
            columns=[
                "smiles",
                "parent_id",
                "version_id",
                "mfcd",
                "cas",
            ],
        )
        all_ids = set(current_listing.version_id.to_list())
        simmate_ids = set(
            cls.objects.filter(is_building_block=True)
            .values_list("id", flat=True)
            .all()
        )

        # if we only want to update the current db, then we cut down the current
        # listing ids to only those that are *missing* from the simmate db
        if update_only:
            update_only_ids = all_ids - simmate_ids
            current_listing = current_listing[
                current_listing.version_id.isin(update_only_ids)
            ]

        # split the ids we need to update into chunks to make things easier
        # on the database (rather than making millions of db_objs in one go)
        chunk_size = 25_000
        nchunk = 0
        nchunks_total = (len(current_listing) // chunk_size) + 1
        failed_rows = []
        for emol_chunk in chunk_list(current_listing, chunk_size):

            logging.info(f"CHUNK # {nchunk} of {nchunks_total}")
            nchunk += 1

            logging.info("Generating database objects...")
            db_objs = []
            for i, row in track(emol_chunk.iterrows(), total=len(emol_chunk)):
                try:
                    molecule = ToolkitMolecule.from_smiles(row.smiles)
                    molecule_db = cls.from_toolkit(
                        id=row.version_id,
                        emol_parent_id=row.parent_id,
                        molecule=molecule,
                        molecule_original=row.smiles,
                        is_building_block=True,
                        is_active_listing=True,
                        cas_number_original=row.cas,
                        mfcd=row.mfcd,
                    )
                    db_objs.append(molecule_db)
                except:
                    failed_rows.append(row.to_dict())

            logging.info("Saving to Simmate database...")
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
                # BUG: is it possible for a structure to change...?
                # update_conflicts=True,
                # unique_fields=["id"],
                # update_fields=[...],
            )

            # logging.info("Adding molecule fingerprints...")
            # cls.populate_fingerprint_database()
            # disabled until I have enough disk space. Would take >100GB

        logging.info("Done!")
        return failed_rows
