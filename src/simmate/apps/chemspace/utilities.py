# -*- coding: utf-8 -*-

import logging
import warnings
from pathlib import Path

import boto3
from botocore.config import Config
from rich.progress import track

from simmate.configuration import settings
from simmate.utilities import get_directory


def download_raw_files(ssl_verify: bool = True):

    if not ssl_verify:
        # Suppress SSL warnings for verify=False below
        warnings.filterwarnings("ignore")

    assert settings.chemspace.mode == "s3"

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.chemspace.s3.access_key,
        aws_secret_access_key=settings.chemspace.s3.secret_key,
        endpoint_url=settings.chemspace.s3.url,
        config=Config(signature_version="s3v4"),
        verify=ssl_verify,
    )

    for bucket_name, prefix in settings.chemspace.s3.buckets.items():

        logging.info(f"Starting downloads for '{bucket_name}': '{prefix}'")

        # only 1_000 filenames can be grabbed at a time, so we need to grab them in pages
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
            local_filename = Path(filename)
            get_directory(local_filename.parent)  # create local directory
            if local_filename.exists():
                continue  # Skip if already downloaded
            s3_client.download_file(
                Bucket=bucket_name,
                Key=filename,
                Filename=str(local_filename),
            )
