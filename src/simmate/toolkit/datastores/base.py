# -*- coding: utf-8 -*-

import functools
import logging
import shutil
from collections import defaultdict
from pathlib import Path

import polars

from simmate.config import settings
from simmate.utils import dispatch, filter_polars_df, get_chunk_key, get_directory


def update_column(column_name: str):
    """
    Decorator for Datastore class methods.
    Iterates through all rows (chunk by chunk) and applies the decorated method
    to add or update a column.

    The decorated method should accept `(cls, df: polars.DataFrame, **kwargs)`
    and return a Polars Series or list containing the new column values.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(cls, parallel_job: bool = False, *args, **kwargs):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                new_values = func(cls, df, *args, **kwargs)
                return df.with_columns(
                    polars.Series(name=column_name, values=new_values)
                )

            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator


def update_table():
    """
    Decorator for Datastore class methods.
    Iterates through all rows (chunk by chunk) and applies the decorated method
    to modify the table.

    The decorated method should accept `(cls, df: polars.DataFrame, **kwargs)`
    and return the updated Polars DataFrame.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(cls, parallel_job: bool = False, *args, **kwargs):
            def transform(df: polars.DataFrame) -> polars.DataFrame:
                return func(cls, df, *args, **kwargs)

            cls._process_chunks(transform, parallel_job)

        return classmethod(wrapper)

    return decorator


class Datastore:
    """
    Base class for datasets containing millions of rows where memory, parsing,
    and fast search times are an issue.
    """

    app_name: str = None
    """
    The name of the app that this datastore belongs to. This is used to
    organize datastores into subdirectories of the simmate base directory
    (e.g. ~/simmate/chembl/datastores/)
    """

    datastore_name: str = None
    """
    The name of the datastore. This is used to organize datastores into
    subdirectories of the simmate base directory 
    (e.g. ~/simmate/chembl/datastores/molecules)

    Use the `directory` property for the more robust Path object
    """

    num_chunks: int = 1000
    """
    Number of chunks used when hashing string IDs to chunk_keys.
    """

    datastore_id_multiplier: int = 1_000_000_000
    """
    Multiplier used to offset the row index by chunk_key when generating datastore_id.
    """

    compression_mode: str = "zstd"  # or "lz4"
    # comparison of file with 5mil rows + SMILES:
    #
    # zstd: 108mb
    # %timeit df = polars.read_parquet("test-zstd.parquet")
    # 394 ms ± 20.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
    #
    # lz4: 217mb
    # %timeit df = polars.read_parquet("test-zstd.parquet")
    # 229 ms ± 15.9 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
    #
    # so... you decide between 2x disk or 2x read speed

    # -------------------------------------------------------------------------

    # file/dir names

    @classmethod
    @property
    def base_directory(cls) -> Path:
        """
        Path object of the directory where all datastore components (live, staging, old) are stored.
        """
        if cls.app_name:
            path = (
                settings.config_directory
                / cls.app_name
                / "datastores"
                / cls.datastore_name
            )
        else:
            path = settings.config_directory / "datastores" / cls.datastore_name

        return get_directory(path)

    @classmethod
    @property
    def directory(cls) -> Path:
        """
        Alias for base_directory for backwards compatibility.
        """
        return cls.base_directory

    @classmethod
    @property
    def live_directory(cls) -> Path:
        """Directory for active parquet chunk files."""
        return cls.base_directory / "live"

    @classmethod
    @property
    def staging_directory(cls) -> Path:
        """Directory for staging new/updated parquet chunk files."""
        return get_directory(cls.base_directory / "staging")

    @classmethod
    @property
    def old_directory(cls) -> Path:
        """Directory for backing up previous live parquet chunk files."""
        return cls.base_directory / "old"

    @classmethod
    @property
    def chunk_files(cls) -> list[Path]:
        """
        Returns a sorted list of existing parquet chunk files in the live directory.
        """
        chunk_files = [f for f in cls.live_directory.rglob("*.parquet") if f.is_file()]
        return sorted(chunk_files, key=lambda f: f.name)

    @classmethod
    @property
    def chunk_files_wildcard(cls) -> Path:
        """
        Wildcard path object for the live directory + all parquet files in it.
        """
        return cls.live_directory / "**" / "*.parquet"

    # -------------------------------------------------------------------------

    @classmethod
    def promote_staging(cls):
        """
        Promotes the staging directory to live, moving the current live
        directory to old.
        """
        # 1. Remove old_directory if it exists
        if cls.old_directory.exists():
            shutil.rmtree(cls.old_directory)

        # 2. Rename live to old
        if cls.live_directory.exists():
            cls.live_directory.rename(cls.old_directory)

        # 3. Rename staging to live
        if cls.staging_directory.exists():
            cls.staging_directory.rename(cls.live_directory)

    @classmethod
    def get_chunk_file(cls, chunk_key: int) -> Path:
        """
        Locates the parquet file corresponding to a given chunk_key.
        """
        # Try to find a hive-partitioned file
        hive_dir = cls.live_directory / f"chunk_key={chunk_key}"
        if hive_dir.exists() and hive_dir.is_dir():
            files = list(hive_dir.glob("*.parquet"))
            if files:
                return files[0]

        # Try to find sequentially numbered file
        seq_file = cls.live_directory / f"{str(chunk_key).zfill(10)}.parquet"
        if seq_file.exists():
            return seq_file

        raise FileNotFoundError(
            f"Could not locate chunk parquet for chunk_key={chunk_key}"
        )

    @classmethod
    def _process_chunks(cls, transform_func, parallel_job: bool = False):
        """
        Iterates through chunk files, applies a transformation to each DataFrame,
        and saves the result to the staging directory.
        """
        files_to_process = []
        output_paths = {}
        for file in cls.chunk_files:
            rel_path = file.relative_to(cls.live_directory)
            output_path = cls.staging_directory / rel_path
            output_paths[file] = output_path
            if not output_path.exists():
                files_to_process.append(file)

        def worker(file_path: Path):
            output_path = output_paths[file_path]
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df = transform_func(polars.read_parquet(file_path))
            df.write_parquet(output_path, compression=cls.compression_mode)

        dispatch(files_to_process, worker, parallel_job)

    # -------------------------------------------------------------------------

    @classmethod
    @property
    def lf(cls) -> polars.LazyFrame:
        """
        Returns a polars.LazyFrame for the datastore using scan_parquet.
        """
        is_hive = cls.live_directory.exists() and any(
            "=" in d.name for d in cls.live_directory.iterdir() if d.is_dir()
        )
        return polars.scan_parquet(
            str(cls.chunk_files_wildcard),
            hive_partitioning=is_hive,
        )

    @classmethod
    def filter(cls, **kwargs) -> polars.LazyFrame:
        """
        Filters the Datastore using django-like ORM queries.
        """

        keys = list(kwargs.keys())
        if len(keys) == 1 and keys[0] in [
            "id",
            "id__exact",
            "id__in",
            "datastore_id",
            "datastore_id__exact",
            "datastore_id__in",
        ]:
            key = keys[0]
            val = kwargs[key]
            vals = val if key.endswith("__in") else [val]

            chunk_keys = {
                (
                    cls._datastore_id_to_chunk_key(v)
                    if key.startswith("datastore_id")
                    else cls._id_to_chunk_key(v)
                )
                for v in vals
            }
            lf = cls.lf.filter(polars.col("chunk_key").is_in(list(chunk_keys)))
            return filter_polars_df(lf, **kwargs)

        return filter_polars_df(cls.lf, **kwargs)

    @classmethod
    def get_row(cls, datastore_id: int) -> polars.DataFrame:
        """
        Retrieves a single row by its datastore_id using basic polars filtering.
        Does not require reading/rewriting the entire chunk.
        """
        chunk_key = cls._datastore_id_to_chunk_key(datastore_id)
        return cls.lf.filter(
            (polars.col("chunk_key") == chunk_key)
            & (polars.col("datastore_id") == datastore_id)
        ).collect()

    @classmethod
    def sample(cls, n: int = 1_000) -> polars.DataFrame:
        """
        Returns a random sample of n rows from the datastore.
        """
        return polars.read_parquet(cls.chunk_files[0], n_rows=n)

    @classmethod
    @property
    def schema(cls) -> polars.Schema:
        """
        Returns the schema (column names and types) from the first chunk file.
        """
        return polars.read_parquet_schema(cls.chunk_files[0])

    @classmethod
    def count(cls) -> int:
        """
        Returns the total number of rows across all chunk files.
        """
        return cls.lf.select(polars.len()).collect().item()

    # -------------------------------------------------------------------------

    @classmethod
    def update_row(cls, datastore_id: int, updates: dict):
        """
        Updates a specific row by its datastore_id. Only loads and rewrites
        the specific chunk parquet file.
        """
        chunk_key = cls._datastore_id_to_chunk_key(datastore_id)
        file = cls.get_chunk_file(chunk_key)

        df = polars.read_parquet(file)
        for col, val in updates.items():
            df = df.with_columns(
                polars.when(polars.col("datastore_id") == datastore_id)
                .then(polars.lit(val))
                .otherwise(polars.col(col))
                .alias(col)
            )
        df.write_parquet(file, compression=cls.compression_mode)

    @classmethod
    def update_rows_bulk(cls, ids_to_update: list[int], updates: dict):
        """
        Evaluates the datastore_ids ahead of time to get a list of chunks,
        then iterates and updates those chunks individually.
        """

        chunk_key_to_ids = defaultdict(list)
        for datastore_id in ids_to_update:
            chunk_key = cls._datastore_id_to_chunk_key(datastore_id)
            chunk_key_to_ids[chunk_key].append(datastore_id)

        for chunk_key, ids in chunk_key_to_ids.items():
            file = cls.get_chunk_file(chunk_key)
            ids_series = polars.Series(ids)

            df = polars.read_parquet(file)
            for col, val in updates.items():
                df = df.with_columns(
                    polars.when(polars.col("datastore_id").is_in(ids_series))
                    .then(polars.lit(val))
                    .otherwise(polars.col(col))
                    .alias(col)
                )
            df.write_parquet(file, compression=cls.compression_mode)

    # -------------------------------------------------------------------------

    @classmethod
    def rename_columns(cls, mapping: dict, parallel_job: bool = False):
        """
        Renames a column across all chunk files.
        """
        cls._process_chunks(lambda df: df.rename(mapping), parallel_job)

    @classmethod
    def drop_column(cls, column_name: str | list[str], parallel_job: bool = False):
        """
        Drops a column (or list of columns) across all chunk files.
        """
        cls._process_chunks(lambda df: df.drop(column_name), parallel_job)

    # update_column - decorator
    # update_table - decorator

    # -------------------------------------------------------------------------

    @classmethod
    def repartition(
        cls,
        partition_columns: str | list[str],
    ):
        """
        Scans all parquets in the live directory and sinks them to the staging
        directory using hive partitioning based on the provided columns.
        """
        cls.lf.sink_parquet(
            polars.PartitionBy(
                base_path=cls.staging_directory,
                key=partition_columns,
            ),
            mkdir=True,
        )
        logging.info("Repartition complete!")

    @classmethod
    def repartition_slow(
        cls,
        partition_column: str,
        partition_values: list = None,
        parallel_job: bool = False,
    ):
        """
        Manual alternative to repartition: iterates over each
        partition value, filters the parquets, and writes a combined.parquet per chunk.
        """

        if partition_values is None:
            logging.info(f"Looking up distinct values for {partition_column}...")
            partition_values = (
                cls.lf.select(partition_column)
                .unique()
                .collect()[partition_column]
                .to_list()
            )

        def _repartition_single_value(val):
            output_dir = cls.staging_directory / f"{partition_column}={val}"
            output_path = output_dir / "combined.parquet"
            if output_path.exists():
                logging.info(f"Skipping {partition_column}={val} - already done.")
                return

            output_dir.mkdir(parents=True, exist_ok=True)

            df = cls.lf.filter(polars.col(partition_column) == val).collect()

            if len(df) == 0:
                logging.info(f"Skipping {partition_column}={val} - no rows found.")
                return

            df.write_parquet(output_path, compression=cls.compression_mode)
            logging.info(f"Repartitioned {partition_column}={val} | Rows: {len(df):,}")

        dispatch(partition_values, _repartition_single_value, parallel_job)

    # -------------------------------------------------------------------------

    @classmethod
    def _datastore_id_to_chunk_key(cls, datastore_id: int) -> int:
        """
        Converts a datastore_id to its corresponding chunk_key.
        """
        return datastore_id // cls.datastore_id_multiplier

    @classmethod
    def _id_to_chunk_key(cls, string_id: str) -> int:
        """
        Converts a string ID to its corresponding chunk_key.
        """
        return get_chunk_key(string_id, cls.num_chunks)

    @update_column(column_name="chunk_key")
    def add_chunk_key_column(
        cls,
        df: polars.DataFrame,
        source_column: str = "id",
        num_chunks: int = None,
    ):
        """
        Helper method that uses get_chunk_key to generate a new column.
        """
        num_chunks = num_chunks or cls.num_chunks

        return df[source_column].map_elements(
            lambda x: get_chunk_key(x, num_chunks),
            return_dtype=polars.Int32,
        )

    @update_column(column_name="datastore_id")
    def add_datastore_id_column(cls, df: polars.DataFrame):
        """
        Helper method to assign a unique sequential integer ID per row, offsetting
        the ID by a chunk_key multiplier. Uses update_column.
        """
        return (
            df.with_row_index("_row_idx").with_columns(
                (
                    polars.col("_row_idx").cast(polars.UInt64)
                    + polars.col("chunk_key").cast(polars.UInt64)
                    * polars.lit(cls.datastore_id_multiplier, dtype=polars.UInt64)
                ).alias("datastore_id")
            )
        )["datastore_id"]
