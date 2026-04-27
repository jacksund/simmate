# -*- coding: utf-8 -*-

import bz2
import logging
import warnings
from pathlib import Path

import boto3
import polars
from botocore.config import Config
from rich.progress import track

from simmate.config import settings
from simmate.utils import get_directory


class ChemspaceClient:
    """
    A client for downloading and accessing data from the ChemSpace database.

    This client handles the download of ChemSpace source files from S3 and
    provides methods for yielding molecule data as polars DataFrames.
    """

    @staticmethod
    def download_source_data(
        bucket_name: str = None,
        prefix: str = None,
        target_dir: str | Path = None,
        ssl_verify: bool = False,
    ) -> Path:
        """
        Downloads ChemSpace source files from S3.

        Args:
            bucket_name (str, optional): The name of the S3 bucket.
            prefix (str, optional): The prefix for the S3 bucket.
            target_dir (str | Path, optional): The directory to download files to.
            ssl_verify (bool, optional): Whether to verify SSL certificates.
                Defaults to False.

        Returns:
            Path: The directory where the files were downloaded.
        """
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

    @classmethod
    def get_freedom_ro5_data(cls, source_dir: str | Path = None):
        """
        Yields chunks of molecule data from the ChemSpace Freedom Ro5 dataset.

        Args:
            source_dir (str | Path, optional): The directory where the
                source files are located. If None, it uses the default
                directory.

        Yields:
            polars.DataFrame: A DataFrame containing a chunk of molecule data.
        """
        if source_dir is None:
            source_dir = settings.config_directory / "chemspace"
        source_dir = Path(source_dir)

        all_files = [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        for i, file in enumerate(all_files):
            logging.info(f"Reading file {i+1} of {len(all_files)}: {file.name}")
            with bz2.open(file, "rb") as f_in:
                file_content = f_in.read()
                df = polars.read_csv(file_content, separator="\t")
                yield df
