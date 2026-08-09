# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.config import settings
from simmate.database.external_connectors.s3 import S3Bucket
from simmate.utils import get_directory


class ChemspaceClient(S3Bucket):
    """
    A client for downloading and accessing data from the ChemSpace database.

    This client handles the download of ChemSpace source files from S3 and
    provides methods for yielding molecule data as polars DataFrames.
    """

    access_key = settings.chemspace.s3.access_key
    secret_key = settings.chemspace.s3.secret_key
    endpoint_url = settings.chemspace.s3.url
    verify = False
    signature_version = "s3v4"

    @classmethod
    def download_source_data(cls):
        """
        Downloads ChemSpace source files from S3.

        Args:
            bucket_name: The name of the S3 bucket.
            prefix: The prefix for the S3 bucket.

        Returns:
            The directory where the files were downloaded.
        """
        target_dir = get_directory(Path(settings.chemspace.datastore_dir) / "raw")
        for bkt, pfx in settings.chemspace.s3.buckets.items():
            cls.sync_directory(target_dir, s3_prefix=pfx, bucket=bkt)

    @classmethod
    def get_freedom_ro5_data(cls, source_dir: str | Path = None):
        """
        Yields chunks of molecule data from the ChemSpace Freedom Ro5 dataset.

        Args:
            source_dir: The directory where the source files are located.

        Yields:
            A polars DataFrame containing a chunk of molecule data.
        """
        if source_dir is None:
            source_dir = Path(settings.chemspace.datastore_dir) / "raw"
        source_dir = Path(source_dir)

        all_files = (
            [source_dir]
            if source_dir.is_file()
            else [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        )

        for i, file in enumerate(all_files):
            logging.info(f"Reading file {i+1} of {len(all_files)}: {file.name}")
            with bz2.open(file, "rb") as f_in:
                file_content = f_in.read()
                yield polars.read_csv(file_content, separator="\t")
