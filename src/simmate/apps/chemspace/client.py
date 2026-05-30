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

    # STEP 1

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
                    tags=["simmate"],
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
        dest_key = source_key.replace(".bz2", ".parquet")
        s3_client = boto3.client("s3")

        # check if the file already exists in the destination
        try:
            s3_client.head_object(Bucket=destination_bucket, Key=dest_key)
            logging.info(f"Skipping {dest_key} as it already exists.")
            return
        except:
            # 404 error means the file does not exist, so we can proceed
            pass

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

        s3_client.upload_fileobj(buffer, destination_bucket, dest_key)

        logging.info(f"Uploaded {dest_key}")

    # -------------------------------------------------------------------------

    # STEP 1b - bugfix

    @classmethod
    def patch_h19_part1_header_rows(
        cls,
        destination_bucket: str = "eks-rd-prod-simmate",
        parquet_key: str = "Freedom_Space_4/Beyond_rule_of_5/2_comp_space/HAC_19/H19_1_PART.smi.parquet",
    ):
        """
        Patches H19_1_PART.smi.parquet which was written with duplicate header
        rows scattered throughout the data (the source bz2 contained repeated
        column-name lines).  Removes those rows, casts numeric columns to their
        correct types, and overwrites the file in the destination bucket.
        """
        s3_client = boto3.client("s3")

        logging.info(f"Downloading {parquet_key} from {destination_bucket}...")
        response = s3_client.get_object(Bucket=destination_bucket, Key=parquet_key)
        buffer_in = io.BytesIO(response["Body"].read())

        df = polars.read_parquet(buffer_in)
        logging.info(f"Loaded shape before patch: {df.shape}")

        # Rows where SMILES equals the literal string "SMILES" are header rows
        # that were accidentally included in the data.
        df = df.filter(polars.col("SMILES") != "SMILES")
        logging.info(f"Shape after removing header rows: {df.shape}")

        float_cols = ["MW", "LogP", "FSP3", "TPSA"]
        int_cols = ["Components", "HAC", "HBA", "HBD", "RotBonds", "reaction_id"]
        df = df.with_columns(
            [polars.col(c).cast(polars.Float64) for c in float_cols]
            + [polars.col(c).cast(polars.Int64) for c in int_cols]
        )

        buffer_out = io.BytesIO()
        df.write_parquet(buffer_out)
        buffer_out.seek(0)

        logging.info(f"Uploading patched file to {destination_bucket}/{parquet_key}...")
        s3_client.upload_fileobj(buffer_out, destination_bucket, parquet_key)
        logging.info(f"Done. Final shape: {df.shape}")

    # -------------------------------------------------------------------------

    # STEP 2a - Ro5/Components/HAC hive partitioning

    @classmethod
    def reorg_to_hive_partitioning(cls, parallel_job: bool = False):
        bucket_name = "eks-rd-prod-simmate"
        source_prefix = "Freedom_Space_4"
        target_prefix = f"s3://{bucket_name}/chemspace_freedom_4"

        s3_client = boto3.client("s3")

        logging.info("Scanning source files...")
        all_keys = cls._list_s3_keys(
            s3_client, bucket_name, source_prefix, suffix=".parquet"
        )

        logging.info("Scanning existing output files...")
        existing_keys = cls._list_s3_keys(
            s3_client, bucket_name, "chemspace_freedom_4", suffix=".parquet"
        )
        processed_hashes = {Path(k).stem.split("_")[0] for k in existing_keys}
        logging.info(f"  {len(processed_hashes)} source files already converted")

        files_to_process = [
            k for k in all_keys if get_hash_key(k) not in processed_hashes
        ]
        logging.info(
            f"  {len(files_to_process)} files to convert "
            f"({len(all_keys) - len(files_to_process)} skipped)"
        )

        if parallel_job:

            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            logging.info(f"Submitting {len(files_to_process)} jobs to the queue...")
            for key in files_to_process:
                SimmateExecutor.submit(
                    cls._reorg_single_file,
                    source_key=key,
                    bucket_name=bucket_name,
                    target_prefix=target_prefix,
                    tags=["simmate"],
                )
        else:
            for key in track(files_to_process):
                cls._reorg_single_file(
                    source_key=key,
                    bucket_name=bucket_name,
                    target_prefix=target_prefix,
                )

        logging.info("Migration complete!")

    @classmethod
    def _reorg_single_file(
        cls,
        source_key: str,
        bucket_name: str = "eks-rd-prod-simmate",
        target_prefix: str = None,
    ):
        if target_prefix is None:
            target_prefix = f"s3://{bucket_name}/chemspace_freedom_4"

        parts = source_key.split("/")
        try:
            base_idx = parts.index("Freedom_Space_4")
            ro5_str = parts[base_idx + 1]
            ro5_bool = False if "beyond" in ro5_str.lower() else True
            comp_val = int(parts[base_idx + 2].replace("_comp_space", ""))
            hac_val = int(parts[base_idx + 3].replace("HAC_", ""))
        except (ValueError, IndexError):
            logging.info(f"Skipping {source_key} - structure mismatch.")
            return

        source_hash = get_hash_key(source_key)

        s3_client = boto3.client("s3")
        partition_prefix = (
            f"chemspace_freedom_4/Ro5={str(ro5_bool).lower()}"
            f"/Components={comp_val}/HAC={hac_val}/{source_hash}"
        )
        if cls._list_s3_keys(s3_client, bucket_name, partition_prefix):
            logging.info(f"Skipping {source_hash[:8]} - already exists.")
            return

        df = polars.read_parquet(f"s3://{bucket_name}/{source_key}").with_columns(
            [
                polars.lit(ro5_bool, dtype=polars.Boolean).alias("Ro5"),
                polars.lit(comp_val, dtype=polars.Int32).alias("Components"),
                polars.lit(hac_val, dtype=polars.Int32).alias("HAC"),
            ]
        )

        df.write_parquet(
            file=target_prefix,
            use_pyarrow=True,
            pyarrow_options={
                "partition_cols": ["Ro5", "Components", "HAC"],
                "existing_data_behavior": "overwrite_or_ignore",
                "basename_template": f"{source_hash}_{{i}}.parquet",
            },
        )

        logging.info(
            f"Migrated: Ro5={ro5_bool}, Comp={comp_val}, HAC={hac_val} "
            f"| Rows: {len(df):,} | Hash: {source_hash[:8]}..."
        )

    # -------------------------------------------------------------------------

    # STEP 2b - chunk IDs for hive partitioning
    # 2_556_764_802 // 5_000_000 = 511
    num_chunks = 500

    @classmethod
    def scatter_to_chunk_partitions(
        cls,
        parallel_job: bool = False,
        scatter_batch_size: int = 10,
    ):
        """
        Pass 1 of step 2b: reads batches of parquets from Freedom_Space_4/, computes
        a chunk_key for every row via get_chunk_key on the ID column, and writes
        hive-partitioned output to chemspace_chunks/chunk_key={N}/*.parquet.

        Source files are processed in batches of scatter_batch_size to reduce the
        total number of small S3 writes (10x fewer files vs. per-file scatter).
        Run combine_chunk_partitions() after all scatter jobs complete.
        """
        bucket_name = "eks-rd-prod-simmate"
        source_prefix = "Freedom_Space_4"
        target_prefix = "chemspace_chunks"

        s3_client = boto3.client("s3")

        logging.info("Scanning source files...")
        all_keys = cls._list_s3_keys(
            s3_client, bucket_name, source_prefix, suffix=".parquet"
        )
        logging.info(f"  Found {len(all_keys)} source parquet files")

        logging.info("Scanning existing scatter output files...")
        existing_keys = cls._list_s3_keys(
            s3_client, bucket_name, target_prefix, suffix=".parquet"
        )
        processed_hashes = {Path(k).stem.split("_")[0] for k in existing_keys}
        logging.info(f"  {len(processed_hashes)} batches already scattered")

        files_to_process = [
            k for k in all_keys if get_hash_key(k) not in processed_hashes
        ]
        logging.info(
            f"  {len(files_to_process)} files to scatter "
            f"({len(all_keys) - len(files_to_process)} skipped)"
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
                    cls._scatter_batch,
                    source_keys=batch,
                    bucket_name=bucket_name,
                    tags=["simmate"],
                )
        else:
            for batch in track(batches):
                cls._scatter_batch(source_keys=batch, bucket_name=bucket_name)

        logging.info("Scatter complete!")

    @classmethod
    def _scatter_batch(
        cls,
        source_keys: list[str],
        bucket_name: str = "eks-rd-prod-simmate",
    ):
        batch_hash = get_hash_key(source_keys[0])

        frames = []
        for key in source_keys:
            frame = polars.read_parquet(f"s3://{bucket_name}/{key}").with_columns(
                polars.lit(
                    False if "beyond" in key.lower() else True,
                    dtype=polars.Boolean,
                ).alias("Ro5")
            )
            frames.append(frame)
        df = polars.concat(frames)
        df = df.with_columns(
            polars.col("ID")
            .map_elements(
                lambda x: get_chunk_key(x, cls.num_chunks), return_dtype=polars.Int32
            )
            .alias("chunk_key")
        ).sort("chunk_key")

        df.write_parquet(
            file=f"s3://{bucket_name}/chemspace_chunks/",
            use_pyarrow=True,
            pyarrow_options={
                "partition_cols": ["chunk_key"],
                "existing_data_behavior": "overwrite_or_ignore",
                "basename_template": f"{batch_hash}_{{i}}.parquet",
                "max_partitions": cls.num_chunks + 1,
            },
        )

        logging.info(
            f"Scattered batch {batch_hash[:8]}... | Rows: {len(df):,} | Files: {len(source_keys)}"
        )

    # -------------------------------------------------------------------------

    @classmethod
    def combine_chunk_partitions(cls, parallel_job: bool = False):
        """
        Pass 2 of step 2b: for each chunk_key folder, combines all scatter
        parquets into a single combined.parquet and adds a datastore_id column
        where datastore_id = row_index + (1_000_000_000 * chunk_key).

        Run after scatter_to_chunk_partitions() has fully completed.
        """
        bucket_name = "eks-rd-prod-simmate"
        target_prefix = "chemspace_chunks"

        s3_client = boto3.client("s3")

        logging.info("Scanning for already-combined chunks...")
        sentinel_keys = cls._list_s3_keys(
            s3_client, bucket_name, target_prefix, suffix="combined.parquet"
        )
        done_chunks = set()
        for k in sentinel_keys:
            # key pattern: chemspace_chunks/chunk_key=N/combined.parquet
            for part in k.split("/"):
                if part.startswith("chunk_key="):
                    done_chunks.add(int(part.split("=")[1]))
                    break
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
                    bucket_name=bucket_name,
                    tags=["simmate"],
                )
        else:
            for chunk_key in track(chunks_to_process):
                cls._combine_single_chunk(chunk_key=chunk_key, bucket_name=bucket_name)

        logging.info("Combine complete!")

    @classmethod
    def _combine_single_chunk(
        cls,
        chunk_key: int,
        bucket_name: str = "eks-rd-prod-simmate",
    ):
        sentinel_key = f"chemspace_chunks/chunk_key={chunk_key}/combined.parquet"
        s3_client = boto3.client("s3")

        try:
            s3_client.head_object(Bucket=bucket_name, Key=sentinel_key)
            logging.info(f"Skipping chunk_key={chunk_key} - already combined.")
            return
        except:
            pass

        scatter_prefix = f"chemspace_chunks/chunk_key={chunk_key}"
        scatter_keys = cls._list_s3_keys(
            s3_client, bucket_name, scatter_prefix, suffix=".parquet"
        )
        # exclude any existing combined.parquet in case head_object check was bypassed
        scatter_keys = [k for k in scatter_keys if not k.endswith("combined.parquet")]

        if not scatter_keys:
            logging.info(f"Skipping chunk_key={chunk_key} - no scatter files found.")
            return

        frames = []
        for key in scatter_keys:
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            frames.append(polars.read_parquet(io.BytesIO(response["Body"].read())))

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

        buffer = io.BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)
        s3_client.upload_fileobj(buffer, bucket_name, sentinel_key)

        for key in scatter_keys:
            s3_client.delete_object(Bucket=bucket_name, Key=key)

        logging.info(f"Combined chunk_key={chunk_key} | Rows: {len(df):,}")
