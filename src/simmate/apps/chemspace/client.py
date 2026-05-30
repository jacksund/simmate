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

    num_chunks = 500

    @classmethod
    def convert_source_to_parquet(
        cls,
        source_dir: str | Path = None,
        staging_dir: str | Path = None,
        parallel_job: bool = False,
    ) -> Path:
        """
        Converts each .bz2 source file to a flat parquet in staging_dir (1:1),
        adding Ro5 and chunk_key columns in this step.

        Run download_source_data() first, then run repartition_by_chunk_key()
        after this completes.
        """
        if source_dir is None:
            source_dir = settings.chemspace.raw_data_dir
        source_dir = Path(source_dir)

        if staging_dir is None:
            staging_dir = Path(settings.chemspace.datastore_dir) / "staging"
        staging_dir = get_directory(Path(staging_dir))

        logging.info("Scanning source .bz2 files...")
        all_files = [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        logging.info(f"  Found {len(all_files)} source .bz2 files")

        processed_hashes = {p.stem for p in staging_dir.glob("*.parquet")}
        logging.info(f"  {len(processed_hashes)} files already converted")

        files_to_process = [
            f for f in all_files if get_hash_key(str(f)) not in processed_hashes
        ]
        logging.info(
            f"  {len(files_to_process)} files to convert "
            f"({len(all_files) - len(files_to_process)} skipped)"
        )

        if parallel_job:
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(files_to_process)} jobs to the queue...")
            for f in files_to_process:
                SimmateExecutor.submit(
                    cls._convert_single_source,
                    file_path=f,
                    staging_dir=staging_dir,
                    tags=["simmate"],
                )
        else:
            for f in track(files_to_process):
                cls._convert_single_source(file_path=f, staging_dir=staging_dir)

        logging.info("Conversion complete!")
        return staging_dir

    @classmethod
    def _convert_single_source(
        cls, file_path: str | Path, staging_dir: str | Path = None
    ):
        file_path = Path(file_path)

        if staging_dir is None:
            staging_dir = get_directory(
                Path(settings.chemspace.datastore_dir) / "staging"
            )
        staging_dir = Path(staging_dir)

        output_path = staging_dir / f"{get_hash_key(str(file_path))}.parquet"
        if output_path.exists():
            logging.info(f"Skipping {file_path.name} - already converted.")
            return

        with bz2.open(file_path, "rb") as f_in:
            df = polars.read_csv(f_in.read(), separator="\t", infer_schema_length=None)

        # BUG-FIX: Their first file has many header rows scattered through
        if "H19_1_PART" in file_path.name:
            float_cols = ["MW", "LogP", "FSP3", "TPSA"]
            int_cols = ["Components", "HAC", "HBA", "HBD", "RotBonds", "reaction_id"]
            df = df.filter(polars.col("SMILES") != "SMILES").with_columns(
                [polars.col(c).cast(polars.Float64) for c in float_cols]
                + [polars.col(c).cast(polars.Int64) for c in int_cols]
            )

        df = df.with_columns(
            polars.lit(
                False if "beyond" in file_path.name.lower() else True,
                dtype=polars.Boolean,
            ).alias("Ro5"),
            polars.col("ID")
            .map_elements(
                lambda x: get_chunk_key(x, cls.num_chunks), return_dtype=polars.Int32
            )
            .alias("chunk_key"),
        )

        df.write_parquet(output_path)
        logging.info(f"Converted {file_path.name} | Rows: {len(df):,}")

    # -------------------------------------------------------------------------

    @classmethod
    def repartition_by_chunk_key(
        cls,
        staging_dir: str | Path = None,
        output_dir: str | Path = None,
    ):
        """
        Scans all staging parquets and sinks them to output_dir partitioned by
        chunk_key. Run after convert_source_to_parquet() has fully completed.
        """
        if staging_dir is None:
            staging_dir = Path(settings.chemspace.datastore_dir) / "staging"
        staging_dir = Path(staging_dir)

        if output_dir is None:
            output_dir = Path(settings.chemspace.datastore_dir)
        output_dir = get_directory(Path(output_dir))

        source_glob = str(staging_dir / "*.parquet")
        logging.info(f"Scanning: {source_glob}")

        lf = polars.scan_parquet(source_glob)

        logging.info(f"Sinking to {output_dir} partitioned by chunk_key...")
        lf.sink_parquet(
            polars.PartitionBy(
                base_path=output_dir,
                key="chunk_key",
            ),
            mkdir=True,
        )

        logging.info("Repartition by chunk_key complete!")

    @classmethod
    def repartition_by_chunk_key_test(
        cls,
        staging_dir: str | Path = None,
        output_dir: str | Path = None,
        parallel_job: bool = False,
    ):
        """
        Manual alternative to repartition_by_chunk_key: iterates over each
        chunk_key, filters the staging parquets, adds a datastore_id column,
        and writes a combined.parquet per chunk.
        """
        if staging_dir is None:
            staging_dir = Path(settings.chemspace.datastore_dir) / "staging"
        staging_dir = Path(staging_dir)

        if output_dir is None:
            output_dir = Path(settings.chemspace.datastore_dir)
        output_dir = get_directory(Path(output_dir))

        done_chunks = {
            int(p.parent.name.split("=")[1])
            for p in output_dir.rglob("combined.parquet")
        }
        chunks_to_process = [c for c in range(cls.num_chunks) if c not in done_chunks]
        logging.info(
            f"  {len(done_chunks)} chunks already done, "
            f"{len(chunks_to_process)} to process"
        )

        if parallel_job:
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(chunks_to_process)} jobs to the queue...")
            for chunk_key in chunks_to_process:
                SimmateExecutor.submit(
                    cls._repartition_single_chunk_test,
                    chunk_key=chunk_key,
                    staging_dir=staging_dir,
                    output_dir=output_dir,
                    tags=["simmate"],
                )
        else:
            for chunk_key in track(chunks_to_process):
                cls._repartition_single_chunk_test(
                    chunk_key=chunk_key,
                    staging_dir=staging_dir,
                    output_dir=output_dir,
                )

        logging.info("Repartition by chunk_key (test) complete!")

    @classmethod
    def _repartition_single_chunk_test(
        cls,
        chunk_key: int,
        staging_dir: str | Path = None,
        output_dir: str | Path = None,
    ):
        if staging_dir is None:
            staging_dir = Path(settings.chemspace.datastore_dir) / "staging"
        staging_dir = Path(staging_dir)

        if output_dir is None:
            output_dir = Path(settings.chemspace.datastore_dir)

        chunk_dir = get_directory(Path(output_dir) / f"chunk_key={chunk_key}")
        output_path = chunk_dir / "combined.parquet"

        if output_path.exists():
            logging.info(f"Skipping chunk_key={chunk_key} - already done.")
            return

        df = (
            polars.scan_parquet(str(staging_dir / "*.parquet"))
            .filter(polars.col("chunk_key") == chunk_key)
            .collect()
        )

        if len(df) == 0:
            logging.info(f"Skipping chunk_key={chunk_key} - no rows found.")
            return

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

        df.write_parquet(output_path)
        logging.info(f"Repartitioned chunk_key={chunk_key} | Rows: {len(df):,}")

    # -------------------------------------------------------------------------

    @classmethod
    def repartition_by_hac(
        cls,
        source_dir: str | Path = None,
        output_dir: str | Path = None,
    ):
        """
        Rearranges the combined chunk parquets into a new hive partition tree
        keyed by HAC (Heavy Atom Count).

        Scans all combined.parquet files from the chunk_key partitions and
        sinks them to output_dir partitioned by HAC. Run after
        combine_chunk_partitions() has fully completed.
        """
        if source_dir is None:
            source_dir = settings.chemspace.datastore_dir
        source_dir = Path(source_dir)

        if output_dir is None:
            output_dir = (
                Path(settings.chemspace.datastore_dir).parent / "chemspace_by_hac"
            )
        output_dir = get_directory(Path(output_dir))

        source_glob = str(source_dir / "chunk_key=*" / "*.parquet")
        logging.info(f"Scanning: {source_glob}")

        lf = polars.scan_parquet(source_glob, hive_partitioning=True)

        logging.info(f"Sinking to {output_dir} partitioned by HAC...")
        lf.sink_parquet(
            polars.PartitionBy(
                base_path=output_dir,
                key="HAC",
            ),
            mkdir=True,
        )

        logging.info("Repartition by HAC complete!")
