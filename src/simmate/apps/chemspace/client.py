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
from simmate.utils import get_chunk_key, get_directory, get_hash_key


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

        target_dir = get_directory(Path(settings.chemspace.raw_data_dir))

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
            source_dir = settings.chemspace.raw_data_dir
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

    # STEP 2 - chunk IDs for hive partitioning
    # 2_556_764_802 // 5_000_000 = 511
    num_chunks = 500

    @classmethod
    def scatter_source_to_chunks(
        cls,
        source_dir: str | Path = None,
        parallel_job: bool = False,
        scatter_batch_size: int = 5,
    ):
        """
        Reads local .bz2 source files, computes a chunk_key for every row, and
        writes hive-partitioned output to
        settings.chemspace.datastore_dir/chunk_key={N}/*.parquet.

        Source files are processed in batches of scatter_batch_size to reduce the
        total number of small writes. Run download_source_data() first to populate
        source_dir, then run combine_chunk_partitions() after all scatter jobs complete.
        """
        if source_dir is None:
            source_dir = settings.chemspace.raw_data_dir
        source_dir = Path(source_dir)

        target_dir = get_directory(Path(settings.chemspace.datastore_dir))

        logging.info("Scanning source .bz2 files...")
        all_files = [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        logging.info(f"  Found {len(all_files)} source .bz2 files")

        logging.info("Scanning existing scatter output files...")
        existing_parquets = list(target_dir.rglob("*.parquet"))
        processed_hashes = {p.stem.split("_")[0] for p in existing_parquets}
        logging.info(f"  {len(processed_hashes)} batches already scattered")

        files_to_process = [
            f for f in all_files if get_hash_key(str(f)) not in processed_hashes
        ]
        logging.info(
            f"  {len(files_to_process)} files to scatter "
            f"({len(all_files) - len(files_to_process)} skipped)"
        )

        batches = [
            files_to_process[i : i + scatter_batch_size]
            for i in range(0, len(files_to_process), scatter_batch_size)
        ]
        logging.info(
            f"  {len(batches)} batches of up to {scatter_batch_size} files each"
        )

        if parallel_job:
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(batches)} jobs to the queue...")
            for batch in batches:
                SimmateExecutor.submit(
                    cls._scatter_source_batch,
                    file_paths=batch,
                    tags=["simmate"],
                )
        else:
            for batch in batches:
                cls._scatter_source_batch(file_paths=batch)

        logging.info("Scatter complete!")

    @classmethod
    def _scatter_source_batch(cls, file_paths: list[str | Path]):
        file_paths = [Path(p) for p in file_paths]
        target_dir = get_directory(Path(settings.chemspace.datastore_dir))
        batch_hash = get_hash_key(str(file_paths[0]))

        logging.info("Unpacking...")
        frames = []
        for file_path in file_paths:
            with bz2.open(file_path, "rb") as f_in:
                df = polars.read_csv(
                    f_in.read(),
                    separator="\t",
                    infer_schema_length=None,
                )

            # BUG-FIX: Their first file has many header rows scattered through
            if "H19_1_PART" in file_path.name:
                float_cols = ["MW", "LogP", "FSP3", "TPSA"]
                int_cols = [
                    "Components",
                    "HAC",
                    "HBA",
                    "HBD",
                    "RotBonds",
                    "reaction_id",
                ]
                df = df.filter(polars.col("SMILES") != "SMILES").with_columns(
                    [polars.col(c).cast(polars.Float64) for c in float_cols]
                    + [polars.col(c).cast(polars.Int64) for c in int_cols]
                )

            df = df.with_columns(
                polars.lit(
                    False if "beyond" in file_path.name.lower() else True,
                    dtype=polars.Boolean,
                ).alias("Ro5")
            )
            frames.append(df)

        df = polars.concat(frames)
        df = df.with_columns(
            polars.col("ID")
            .map_elements(
                lambda x: get_chunk_key(x, cls.num_chunks), return_dtype=polars.Int32
            )
            .alias("chunk_key")
        ).sort("chunk_key")

        logging.info("Writing...")
        df.write_parquet(
            file=str(target_dir) + "/",
            use_pyarrow=True,
            pyarrow_options={
                "partition_cols": ["chunk_key"],
                "existing_data_behavior": "overwrite_or_ignore",
                "basename_template": f"{batch_hash}_{{i}}.parquet",
                "max_partitions": cls.num_chunks + 1,
            },
        )

        logging.info(
            f"Scattered batch {batch_hash[:8]}... | Rows: {len(df):,} | Files: {len(file_paths)}"
        )

    # -------------------------------------------------------------------------

    @classmethod
    def combine_chunk_partitions(cls, parallel_job: bool = False):
        """
        Pass 2 of step 2b: for each chunk_key folder, combines all scatter
        parquets into a single combined.parquet and adds a datastore_id column
        where datastore_id = row_index + (1_000_000_000 * chunk_key).

        Run after scatter_source_to_chunks() has fully completed.
        """
        target_dir = get_directory(Path(settings.chemspace.datastore_dir))

        logging.info("Scanning for already-combined chunks...")
        done_chunks = {
            int(p.parent.name.split("=")[1])
            for p in target_dir.rglob("combined.parquet")
        }
        logging.info(f"  {len(done_chunks)} chunks already combined")

        chunks_to_process = [c for c in range(cls.num_chunks) if c not in done_chunks]
        logging.info(f"  {len(chunks_to_process)} chunks to combine")

        if parallel_job:
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(chunks_to_process)} jobs to the queue...")
            for chunk_key in chunks_to_process:
                SimmateExecutor.submit(
                    cls._combine_single_chunk,
                    chunk_key=chunk_key,
                    tags=["simmate"],
                )
        else:
            for chunk_key in track(chunks_to_process):
                cls._combine_single_chunk(chunk_key=chunk_key)

        logging.info("Combine complete!")

    @classmethod
    def _combine_single_chunk(cls, chunk_key: int):
        target_dir = Path(settings.chemspace.datastore_dir)
        chunk_dir = target_dir / f"chunk_key={chunk_key}"
        sentinel_path = chunk_dir / "combined.parquet"

        if sentinel_path.exists():
            logging.info(f"Skipping chunk_key={chunk_key} - already combined.")
            return

        scatter_paths = [
            p for p in chunk_dir.glob("*.parquet") if p.name != "combined.parquet"
        ]

        if not scatter_paths:
            logging.info(f"Skipping chunk_key={chunk_key} - no scatter files found.")
            return

        frames = [polars.read_parquet(p) for p in scatter_paths]

        df = polars.concat(frames)
        df = (
            df.with_row_index("_row_idx")
            .with_columns(
                (
                    polars.col("_row_idx").cast(polars.UInt64)
                    + polars.lit(chunk_key * 1_000_000_000, dtype=polars.UInt64)
                ).alias("datastore_id")
            )
            .drop("_row_idx")
        )

        df.write_parquet(sentinel_path)

        for p in scatter_paths:
            p.unlink()

        logging.info(f"Combined chunk_key={chunk_key} | Rows: {len(df):,}")
