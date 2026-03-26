# -*- coding: utf-8 -*-

import logging
import warnings
from pathlib import Path

from simmate.apps.rdkit.models import Molecule
from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData
from simmate.utils import get_directory


class ChemSpaceFreedomSpaceMolecule(ThirdPartyData, Molecule):
    """
    Molecules from the
    [ChemSpace "Freedom Space"](https://chem-space.com/compounds/freedom-space)
    database.
    """

    class Meta:
        db_table = "chemspace__freedom_space__molecules"

    # TODO: Freedom space is now 5bil molecules... The "Screening Compound Catalog"

    external_website = "https://chem-space.com/compounds/freedom-space"
    is_redistribution_allowed = False

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the molecule (ex: "a1_101109_29635")
    """
    # BUG: this is catalog number, but we really want ChemSpaceID

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the ChemSpace website.
        """
        return f"https://chem-space.com/{self.chemspace_id}"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls):
        raise NotImplementedError(
            "We do not yet support loading into a database. Use the datastore instead."
        )

    @classmethod
    def download_source_data(
        cls,
        bucket_name: str = None,
        prefix: str = None,
        target_dir: str | Path = None,
        ssl_verify: bool = False,
    ) -> Path:

        import boto3
        from botocore.config import Config
        from rich.progress import track

        if not ssl_verify:
            warnings.filterwarnings("ignore")

        assert settings.chemspace.mode == "s3"

        if target_dir is None:
            target_dir = settings.config_directory / "chemspace"
        target_dir = get_directory(Path(target_dir))

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.chemspace.s3.access_key,
            aws_secret_access_key=settings.chemspace.s3.secret_key,
            endpoint_url=settings.chemspace.s3.url,
            config=Config(signature_version="s3v4"),
            verify=ssl_verify,
        )

        # Build list of (bucket, prefix) pairs to download
        if bucket_name:
            downloads = [(bucket_name, prefix or "")]
        else:
            downloads = list(settings.chemspace.s3.buckets.items())

        for bucket_name, prefix in downloads:

            logging.info(f"Starting downloads for '{bucket_name}': '{prefix}'")

            # only 1_000 filenames can be grabbed at a time, so we need
            # to grab them in pages
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix,
            )
            all_files = []
            for page in page_iterator:
                if "Contents" in page:
                    all_files.extend(page["Contents"])
            logging.info(f"{len(all_files)} total files found")

            logging.info("Downloading...")
            for file in track(all_files):
                filename = file["Key"]
                if filename.endswith("/"):
                    continue  # skip non-files
                local_filename = target_dir / filename
                get_directory(local_filename.parent)
                if local_filename.exists():
                    continue  # Skip if already downloaded
                s3_client.download_file(
                    Bucket=bucket_name,
                    Key=filename,
                    Filename=str(local_filename),
                )

        return target_dir
