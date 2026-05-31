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

    @classmethod
    def get_source_client(cls):
        """Returns a configured boto3 S3 client for the ChemSpace source bucket."""
        return boto3.client(
            "s3",
            aws_access_key_id=settings.chemspace.s3.access_key,
            aws_secret_access_key=settings.chemspace.s3.secret_key,
            endpoint_url=settings.chemspace.s3.url,
            config=Config(signature_version="s3v4"),
            verify=False,
        )

    @classmethod
    def _list_source_keys(cls, bucket: str, prefix: str = "", client=None) -> list[str]:
        """Returns all non-directory object keys in the given bucket/prefix."""
        if not client:
            client = cls.get_source_client()

        paginator = client.get_paginator("list_objects_v2")
        return [
            obj["Key"]
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
            if not obj["Key"].endswith("/") and obj["Key"].endswith(".bz2")
        ]

    @staticmethod
    def _dispatch(items, fn, parallel: bool, **kwargs):
        """Runs fn(item, **kwargs) for each item, either serially or via SimmateExecutor."""
        if parallel:
            from simmate.database import connect  # isort:skip
            from simmate.compute import SimmateExecutor  # isort:skip

            for item in items:
                SimmateExecutor.submit(fn, item, tags=["simmate"], **kwargs)
        else:
            for item in track(items):
                fn(item, **kwargs)

    @classmethod
    def download_source_data(
        cls,
        bucket_name: str = None,
        prefix: str = None,
    ) -> Path:
        """
        Downloads ChemSpace source files from S3.

        Args:
            bucket_name: The name of the S3 bucket.
            prefix: The prefix for the S3 bucket.
            ssl_verify: Whether to verify SSL certificates.

        Returns:
            The directory where the files were downloaded.
        """
        # mute ssl_verify warnings
        warnings.filterwarnings("ignore")

        assert settings.chemspace.mode == "s3"

        target_dir = get_directory(Path(settings.chemspace.datastore_dir) / "raw")
        downloads = (
            [(bucket_name, prefix or "")]
            if bucket_name
            else list(settings.chemspace.s3.buckets.items())
        )

        client = cls.get_source_client()
        for bkt, pfx in downloads:
            logging.info("Fetching full list of S3 keys...")
            all_keys = cls._list_source_keys(bkt, pfx, client)
            logging.info(f"Downloading {len(all_keys)} files from '{bkt}': '{pfx}'")
            for key in all_keys:
                logging.info(key)
                local_filename = target_dir / key
                get_directory(local_filename.parent)
                if not local_filename.exists():
                    client.download_file(
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

    # -------------------------------------------------------------------------
    # Parquet conversion (dev/ETL)
    # -------------------------------------------------------------------------

    # num_chunks = 20_000
    num_chunks = 80

    @classmethod
    def convert_source_to_parquet(cls, parallel_job: bool = False) -> Path:
        """
        Converts each .bz2 source file to a flat parquet in staging_dir (1:1),
        adding Ro5 and chunk_key columns in this step.

        Run download_source_data() first, then run repartition_by_chunk_key()
        after this completes.
        """
        datastore_dir = Path(settings.chemspace.datastore_dir)
        source_dir = datastore_dir / "raw"
        staging_dir = get_directory(datastore_dir / "staging")

        all_files = [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        processed_hashes = {p.stem for p in staging_dir.glob("*.parquet")}
        files_to_process = [
            f for f in all_files if get_hash_key(str(f)) not in processed_hashes
        ]
        logging.info(
            f"Found {len(all_files)} source files; "
            f"{len(processed_hashes)} already converted, "
            f"{len(files_to_process)} to process"
        )

        cls._dispatch(
            files_to_process,
            cls._convert_single_source,
            parallel_job,
        )
        logging.info("Conversion complete!")
        return staging_dir

    @classmethod
    def _convert_single_source(cls, file_path: str | Path):
        file_path = Path(file_path)
        staging_dir = Path(settings.chemspace.datastore_dir) / "staging"

        output_path = staging_dir / f"{get_hash_key(str(file_path))}.parquet"
        if output_path.exists():
            logging.info(f"Skipping {file_path.name} - already converted.")
            return

        with bz2.open(file_path, "rb") as f_in:
            df = polars.read_csv(
                f_in.read(),
                separator="\t",
                infer_schema_length=None,
            )

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
                lambda x: get_chunk_key(x, cls.num_chunks),
                return_dtype=polars.Int32,
            )
            .alias("chunk_key"),
        )

        df.write_parquet(output_path)
        logging.info(f"Converted {file_path.name} | Rows: {len(df):,}")

    # -------------------------------------------------------------------------

    @classmethod
    def repartition_by_chunk_key_manual(cls, parallel_job: bool = False):
        """
        Manual alternative to repartition_by_chunk_key: iterates over each
        chunk_key, filters the staging parquets, adds a datastore_id column,
        and writes a combined.parquet per chunk.
        """
        output_dir = get_directory(Path(settings.chemspace.datastore_dir) / "live")

        done_chunks = {
            int(p.parent.name.split("=")[1])
            for p in output_dir.rglob("combined.parquet")
        }
        chunks_to_process = [c for c in range(cls.num_chunks) if c not in done_chunks]
        logging.info(
            f"{len(done_chunks)} chunks already done, "
            f"{len(chunks_to_process)} to process"
        )

        cls._dispatch(
            chunks_to_process,
            cls._repartition_single_chunk_test,
            parallel_job,
        )
        logging.info("Repartition by chunk_key complete!")

    @classmethod
    def _repartition_single_chunk_test(cls, chunk_key: int):
        datastore_dir = Path(settings.chemspace.datastore_dir)
        staging_dir = datastore_dir / "staging"

        chunk_dir = get_directory(datastore_dir / "live" / f"chunk_key={chunk_key}")
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
    def repartition_by_hac(cls):
        """
        Rearranges the combined chunk parquets into a new hive partition tree
        keyed by HAC (Heavy Atom Count).

        Scans all combined.parquet files from the chunk_key partitions and
        sinks them to output_dir partitioned by HAC. Run after
        repartition_by_chunk_key_test() has fully completed.
        """
        datastore_dir = Path(settings.chemspace.datastore_dir)
        source_dir = datastore_dir / "live"
        output_dir = get_directory(datastore_dir.parent / "chemspace_by_hac")

        source_glob = str(source_dir / "chunk_key=*" / "*.parquet")
        logging.info(f"Sinking to {output_dir} partitioned by HAC...")
        polars.scan_parquet(source_glob, hive_partitioning=True).sink_parquet(
            polars.PartitionBy(base_path=output_dir, key="HAC"),
            mkdir=True,
        )
        logging.info("Repartition by HAC complete!")

    @classmethod
    def repartition_by_chunk_key(cls):
        """
        Scans all staging parquets and sinks them to output_dir partitioned by
        chunk_key. Run after convert_source_to_parquet() has fully completed.
        """
        datastore_dir = Path(settings.chemspace.datastore_dir)
        staging_dir = datastore_dir / "staging"
        output_dir = get_directory(datastore_dir / "live")

        source_glob = str(staging_dir / "*.parquet")
        logging.info(f"Sinking to {output_dir} partitioned by chunk_key...")
        polars.scan_parquet(source_glob).sink_parquet(
            polars.PartitionBy(
                base_path=output_dir,
                key="chunk_key",
            ),
            mkdir=True,
        )
        logging.info("Repartition by chunk_key complete!")

    # -------------------------------------------------------------------------

    @classmethod
    def add_fingerprints(cls, parallel_job: bool = False):
        """
        Adds MACCS, ECFP4, and FCFP4 fingerprint columns to each chunk's live
        parquet, writing the result as combined_w_fps.parquet alongside the
        existing combined.parquet.

        Run after repartition_by_chunk_key() or repartition_by_chunk_key_manual()
        has fully completed.
        """
        live_dir = Path(settings.chemspace.datastore_dir) / "live"
        done_chunks = {
            int(p.parent.name.split("=")[1])
            for p in live_dir.rglob("combined_w_fps.parquet")
        }
        chunks_to_process = [c for c in range(cls.num_chunks) if c not in done_chunks]
        logging.info(
            f"{len(done_chunks)} chunks already done, "
            f"{len(chunks_to_process)} to process"
        )
        cls._dispatch(
            chunks_to_process,
            cls._add_fingerprints_single_chunk,
            parallel_job,
        )
        logging.info("Fingerprint addition complete!")

    @classmethod
    def _add_fingerprints_single_chunk(cls, chunk_key: int):
        from simmate.toolkit.featurizers import USearchFingerprints

        datastore_dir = Path(settings.chemspace.datastore_dir)
        chunk_dir = datastore_dir / "live" / f"chunk_key={chunk_key}"
        input_path = chunk_dir / "combined.parquet"
        output_path = chunk_dir / "combined_w_fps.parquet"

        if output_path.exists():
            logging.info(f"Skipping chunk_key={chunk_key} - already done.")
            return

        if not input_path.exists():
            logging.info(f"Skipping chunk_key={chunk_key} - no combined.parquet found.")
            return

        df = polars.read_parquet(input_path)
        fingerprints = USearchFingerprints.featurize_many(
            df["SMILES"].to_list(), parallel=True
        )
        maccs_list, ecfp4_list, fcfp4_list = zip(*fingerprints)

        df = df.with_columns(
            polars.Series("maccs", list(maccs_list)),
            polars.Series("ecfp4", list(ecfp4_list)),
            polars.Series("fcfp4", list(fcfp4_list)),
        )

        df.write_parquet(output_path)
        logging.info(
            f"Fingerprints added for chunk_key={chunk_key} | Rows: {len(df):,}"
        )

    # -------------------------------------------------------------------------

    @classmethod
    def build_usearch_index(cls) -> None:
        """
        Builds USearch binary indexes from the combined_w_fps.parquet files.

        Creates one index per fingerprint type and saves them to datastore_dir.
        Run after add_fingerprints() has fully completed.

        Args:
            fp_types: Fingerprint types to index. Defaults to all three:
                ["maccs", "ecfp4", "fcfp4"].
        """
        import numpy
        import pyarrow
        from usearch.index import (
            CompiledMetric,
            Index,
            MetricKind,
            MetricSignature,
            ScalarKind,
        )

        from simmate.toolkit.datastores.numba_funcs import (
            tanimoto_ecfp4,
            tanimoto_maccs,
        )

        datastore_dir = Path(settings.chemspace.datastore_dir)
        live_dir = datastore_dir / "live"
        source_glob = str(live_dir / "chunk_key=*" / "*w_fps.parquet")

        # ndim is bits rounded up to uint32 boundary; stored_bytes is actual bytes
        # from packbits; padded_bytes is stored_bytes zero-padded to uint32 alignment
        fp_configs = {
            "maccs": {
                "ndim": 192,
                "stored_bytes": 21,
                "padded_bytes": 24,
                "metric_fn": tanimoto_maccs,
            },
            # TODO:
            # "ecfp4": {
            #     "ndim": 2048,
            #     "stored_bytes": 256,
            #     "padded_bytes": 256,
            #     "metric_fn": tanimoto_ecfp4,
            # },
            # "fcfp4": {
            #     "ndim": 2048,
            #     "stored_bytes": 256,
            #     "padded_bytes": 256,
            #     "metric_fn": tanimoto_ecfp4,
            # },
        }

        lf = polars.scan_parquet(source_glob, hive_partitioning=True)

        fp_type = "maccs"  # fixed for now
        cfg = fp_configs[fp_type]

        index_path = str(datastore_dir / f"index-{fp_type}.usearch")
        logging.info(f"Building {fp_type} index → {index_path}")

        index = Index(
            ndim=cfg["ndim"],
            dtype=ScalarKind.B1,
            metric=CompiledMetric(
                pointer=cfg["metric_fn"].address,
                kind=MetricKind.Tanimoto,
                signature=MetricSignature.ArrayArray,
            ),
            path=index_path,
        )

        for chunk_key in range(cls.num_chunks):
            logging.info(f"  {fp_type} chunk_key={chunk_key}")
            df = (
                lf.filter(polars.col("chunk_key") == chunk_key)
                .select("datastore_id", fp_type)
                .collect()
            )
            if len(df) == 0:
                continue

            keys = df["datastore_id"].to_numpy()
            if len(index) > 0 and keys[0] in index:
                logging.info(f"Skipping chunk_key={chunk_key} - already indexed.")
                continue

            df_pa = df.to_arrow()
            fps = df_pa.column(fp_type).cast(pyarrow.binary(cfg["stored_bytes"]))

            vectors = []
            for fp in fps:
                vec = numpy.zeros(cfg["padded_bytes"], dtype=numpy.uint8)
                vec[: cfg["stored_bytes"]] = fp.as_buffer()
                vectors.append(vec)
            vectors = numpy.vstack(vectors)

            index.add(
                keys,
                vectors,
                log=f"Building index-{fp_type}.usearch chunk {chunk_key}",
            )

            index.save(index_path)
            logging.info(f"Saved {fp_type} index | Vectors: {len(index):,}")
