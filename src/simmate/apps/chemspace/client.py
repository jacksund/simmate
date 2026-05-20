# -*- coding: utf-8 -*-

import bz2
import io
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

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _get_source_client(cls, ssl_verify: bool = False):
        """Returns a configured boto3 S3 client for the ChemSpace source bucket."""
        return boto3.client(
            "s3",
            aws_access_key_id=settings.chemspace.s3.access_key,
            aws_secret_access_key=settings.chemspace.s3.secret_key,
            endpoint_url=settings.chemspace.s3.url,
            config=Config(signature_version="s3v4"),
            verify=ssl_verify,
        )

    @staticmethod
    def _list_s3_keys(
        s3_client,
        bucket: str,
        prefix: str = "",
        suffix: str = "",
    ) -> list[str]:
        """Paginates and returns all object keys matching the given suffix."""
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

        keys = []
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/") and (not suffix or key.endswith(suffix)):
                    keys.append(key)
        return keys

    @classmethod
    def _get_download_targets(cls) -> list[tuple[str, str]]:
        """Returns list of (bucket, prefix) pairs from settings."""
        return list(settings.chemspace.s3.buckets.items())

    @classmethod
    def _get_targets(cls, bucket_name: str = None, prefix: str = None):
        """Helper to resolve (bucket, prefix) targets."""
        return (
            [(bucket_name, prefix or "")]
            if bucket_name
            else cls._get_download_targets()
        )

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    @classmethod
    def download_source_data(
        cls,
        bucket_name: str = None,
        prefix: str = None,
        target_dir: str | Path = None,
        ssl_verify: bool = False,
    ) -> Path:
        """
        Downloads ChemSpace source files from S3.

        Args:
            bucket_name: The name of the S3 bucket.
            prefix: The prefix for the S3 bucket.
            target_dir: The directory to download files to.
            ssl_verify: Whether to verify SSL certificates.

        Returns:
            The directory where the files were downloaded.
        """
        if not ssl_verify:
            warnings.filterwarnings("ignore")

        assert settings.chemspace.mode == "s3"

        if target_dir is None:
            target_dir = settings.config_directory / "chemspace"
        target_dir = get_directory(Path(target_dir))

        s3_client = cls._get_source_client(ssl_verify)
        downloads = cls._get_targets(bucket_name, prefix)

        for bkt, pfx in downloads:
            logging.info(f"Starting downloads for '{bkt}': '{pfx}'")
            all_keys = cls._list_s3_keys(s3_client, bkt, pfx)
            logging.info(f"{len(all_keys)} total files found")

            logging.info("Downloading...")
            for key in track(all_keys):
                local_filename = target_dir / key
                get_directory(local_filename.parent)
                if not local_filename.exists():
                    s3_client.download_file(
                        Bucket=bkt,
                        Key=key,
                        Filename=str(local_filename),
                    )

        return target_dir

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
            source_dir = settings.config_directory / "chemspace"
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

    # -------------------------------------------------------------------------
    # Parquet conversion (dev/ETL)
    # -------------------------------------------------------------------------

    @classmethod
    def convert_to_parquet(
        cls,
        bucket_name: str = None,
        prefix: str = None,
        destination_bucket: str = "eks-rd-prod-simmate",
        ssl_verify: bool = False,
        parallel_job: bool = False,
    ):
        """
        Converts .bz2 source files to .parquet and uploads to a destination bucket.

        Skips files that already have a corresponding .parquet in the destination.
        """
        if not ssl_verify:
            warnings.filterwarnings("ignore")

        assert settings.chemspace.mode == "s3"

        source_client = cls._get_source_client(ssl_verify)
        downloads = cls._get_targets(bucket_name, prefix)

        all_source_keys = []
        for bkt, pfx in downloads:
            logging.info(f"Listing source files for '{bkt}': '{pfx}'")
            keys = cls._list_s3_keys(source_client, bkt, pfx, suffix=".bz2")
            all_source_keys.extend((bkt, k) for k in keys)
            logging.info(f"  Found {len(keys)} .bz2 files")

        logging.info("Listing existing parquet files in destination bucket...")
        s3_dest = boto3.resource("s3")
        dest_bucket_obj = s3_dest.Bucket(destination_bucket)
        existing_keys = {
            obj.key
            for obj in dest_bucket_obj.objects.all()
            if obj.key.endswith(".parquet")
        }
        logging.info(f"  Found {len(existing_keys)} existing parquet files")

        files_to_process = [
            (bkt, key)
            for bkt, key in all_source_keys
            if key.replace(".bz2", ".parquet") not in existing_keys
        ]
        logging.info(
            f"{len(files_to_process)} files to convert "
            f"({len(all_source_keys) - len(files_to_process)} skipped)"
        )

        if parallel_job:
            
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(files_to_process)} jobs to the queue...")
            for source_bkt, source_key in files_to_process:
                SimmateExecutor.submit(
                    cls._convert_single_file,
                    source_bucket=source_bkt,
                    source_key=source_key,
                    destination_bucket=destination_bucket,
                    ssl_verify=ssl_verify,
                    tags=["chmspce"],
                )
        else:
            for source_bkt, source_key in track(files_to_process):
                cls._convert_single_file(
                    source_bucket=source_bkt,
                    source_key=source_key,
                    destination_bucket=destination_bucket,
                    ssl_verify=ssl_verify,
                )

        logging.info("Done.")

    @classmethod
    def _convert_single_file(
        cls,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        ssl_verify: bool = False,
    ):
        source_client = cls._get_source_client(ssl_verify)

        response = source_client.get_object(Bucket=source_bucket, Key=source_key)
        compressed_data = response["Body"].read()

        decompressed = bz2.decompress(compressed_data)
        df = polars.read_csv(
            decompressed,
            separator="\t",
            infer_schema_length=None,
        )

        buffer = io.BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)

        dest_key = source_key.replace(".bz2", ".parquet")
        s3_dest = boto3.resource("s3")
        dest_bucket_obj = s3_dest.Bucket(destination_bucket)
        dest_bucket_obj.upload_fileobj(buffer, dest_key)

        logging.info(f"Uploaded {dest_key}")
