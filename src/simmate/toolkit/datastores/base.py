# -*- coding: utf-8 -*-

import functools
import logging
import uuid
from pathlib import Path

import polars

from simmate.config import settings
from simmate.utils import chunk_list, get_directory


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
        def wrapper(cls, *args, **kwargs):
            for file in cls.chunk_files:
                df = polars.read_parquet(file)
                new_values = func(cls, df, *args, **kwargs)
                df = df.with_columns(polars.Series(name=column_name, values=new_values))
                df.write_parquet(file, compression=cls.compression_mode)

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
        def wrapper(cls, *args, **kwargs):
            for file in cls.chunk_files:
                df = polars.read_parquet(file)
                df = func(cls, df, *args, **kwargs)
                df.write_parquet(file, compression=cls.compression_mode)

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

    chunk_size: int = 1_000_000
    """
    Number of rows per chunked parquet file
    """

    num_chunks: int = 1000
    """
    Number of chunks used when hashing string IDs to chunk_keys.
    """

    datastore_id_multiplier: int = 1_000_000_000
    """
    Multiplier used to offset the row index by chunk_key when generating datastore_id.
    """

    compression_mode: str = "lz4"  # or "zstd" for slower but smaller files

    @classmethod
    @property
    def directory(cls) -> Path:
        """
        Path object of the directory where all parquet chunk files are stored
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
    def chunk_files(cls) -> list[Path]:
        """
        Returns a sorted list of existing parquet chunk files in the store directory.
        """
        chunk_files = [f for f in cls.directory.rglob("*.parquet") if f.is_file()]
        return sorted(chunk_files, key=lambda f: f.name)

    @classmethod
    @property
    def chunk_files_wildcard(cls) -> Path:
        """
        Wildcard path object for the directory + all parquet files in it.
        """
        return cls.directory / "**" / "*.parquet"

    @classmethod
    @property
    def lf(cls) -> polars.LazyFrame:
        """
        Returns a polars.LazyFrame for the datastore using scan_parquet.
        """
        is_hive = cls.directory.exists() and any(
            "=" in d.name for d in cls.directory.iterdir() if d.is_dir()
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
        from simmate.utils.dataframes import filter_polars_df

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

            is_in_query = key.endswith("__in")
            vals = val if is_in_query else [val]

            chunk_keys = set()
            for v in vals:
                if key.startswith("datastore_id"):
                    chunk_keys.add(cls._datastore_id_to_chunk_key(v))
                else:
                    chunk_keys.add(cls._id_to_chunk_key(v))

            lf = cls.lf.filter(polars.col("chunk_key").is_in(list(chunk_keys)))
            return filter_polars_df(lf, **kwargs)

        return filter_polars_df(cls.lf, **kwargs)

    @classmethod
    def _inflate_data_chunk(
        cls,
        df: polars.DataFrame,
        parallel: bool = True,
    ) -> polars.DataFrame:
        """
        Hook for adding derived properties, methods, and fingerprint columns
        to a chunk before it is written to disk.
        """
        return df

    @classmethod
    def add_dataframe(
        cls,
        df: polars.DataFrame,
        parallel: bool = False,
        target_directory: str | Path = None,
    ):
        """
        Generates calculated properties+features before adding it to the disk
        store. New chunks are saved using UUID filenames. The `reorganize_chunks`
        method should be used to combine and number chunks sequentially.
        """
        output_dir = (
            get_directory(target_directory) if target_directory else cls.directory
        )

        for chunk in chunk_list(df, cls.chunk_size):
            chunk = cls._inflate_data_chunk(chunk, parallel=parallel)
            chunk_filename = output_dir / f"{uuid.uuid4().hex}.parquet"
            chunk.write_parquet(
                chunk_filename,
                compression=cls.compression_mode,
            )

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
        from simmate.utils import get_chunk_key

        return get_chunk_key(string_id, cls.num_chunks)

    @classmethod
    def get_chunk_file(cls, chunk_key: int) -> Path:
        """
        Locates the parquet file corresponding to a given chunk_key.
        """
        # Try to find a hive-partitioned file
        hive_dir = cls.directory / f"chunk_key={chunk_key}"
        if hive_dir.exists() and hive_dir.is_dir():
            files = list(hive_dir.glob("*.parquet"))
            if files:
                return files[0]

        # Try to find sequentially numbered file
        seq_file = cls.directory / f"{str(chunk_key).zfill(10)}.parquet"
        if seq_file.exists():
            return seq_file

        raise FileNotFoundError(
            f"Could not locate chunk parquet for chunk_key={chunk_key}"
        )

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
        chunk_key_to_ids = {}
        for datastore_id in ids_to_update:
            chunk_key = cls._datastore_id_to_chunk_key(datastore_id)
            if chunk_key not in chunk_key_to_ids:
                chunk_key_to_ids[chunk_key] = []
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

    @classmethod
    def rename_column(cls, old_name: str, new_name: str):
        """
        Renames a column across all chunk files.
        """
        for file in cls.chunk_files:
            df = polars.read_parquet(file)
            df = df.rename({old_name: new_name})
            df.write_parquet(file, compression=cls.compression_mode)

    @classmethod
    def drop_column(cls, column_name: str | list[str]):
        """
        Drops a column (or list of columns) across all chunk files.
        """
        for file in cls.chunk_files:
            df = polars.read_parquet(file)
            df = df.drop(column_name)
            df.write_parquet(file, compression=cls.compression_mode)

    @classmethod
    def reorganize_chunks(cls, target_directory: str | Path = None):
        """
        Reorganizes existing parquet files to ensure each chunk matches
        `cls.chunk_size`. Smaller chunks are combined, and larger ones are split.
        """
        directory = (
            get_directory(target_directory) if target_directory else cls.directory
        )

        for f in directory.glob("*.parquet"):
            f.rename(f.parent / (f.name + ".old"))

        old_files = sorted(directory.glob("*.parquet.old"))
        if not old_files:
            logging.info("No files found to reorganize.")
            return

        current_chunk_index = 0
        accumulated_df = None
        total_rows_read = 0
        total_rows_written = 0
        old_files_to_delete = []

        for old_file in old_files:
            df = polars.read_parquet(old_file)
            total_rows_read += len(df)
            old_files_to_delete.append((old_file, total_rows_read))

            if accumulated_df is None:
                accumulated_df = df
            else:
                accumulated_df = polars.concat([accumulated_df, df])

            while len(accumulated_df) >= cls.chunk_size:
                chunk = accumulated_df.head(cls.chunk_size)
                accumulated_df = accumulated_df.tail(
                    len(accumulated_df) - cls.chunk_size
                )

                chunk_filename = (
                    directory / f"{str(current_chunk_index).zfill(10)}.parquet"
                )
                chunk.write_parquet(
                    chunk_filename,
                    compression=cls.compression_mode,
                )
                current_chunk_index += 1
                total_rows_written += cls.chunk_size

                while (
                    old_files_to_delete
                    and total_rows_written >= old_files_to_delete[0][1]
                ):
                    path, _ = old_files_to_delete.pop(0)
                    path.unlink()

        if accumulated_df is not None and len(accumulated_df) > 0:
            chunk_filename = directory / f"{str(current_chunk_index).zfill(10)}.parquet"
            accumulated_df.write_parquet(
                chunk_filename,
                compression=cls.compression_mode,
            )
            total_rows_written += len(accumulated_df)

        while old_files_to_delete and total_rows_written >= old_files_to_delete[0][1]:
            path, _ = old_files_to_delete.pop(0)
            path.unlink()

    @classmethod
    def repartition(
        cls,
        partition_columns: str | list[str],
        source_directory: str | Path = None,
        target_directory: str | Path = None,
    ):
        """
        Scans all parquets in the source directory and sinks them to the target
        directory using hive partitioning based on the provided columns.
        """
        source_dir = (
            get_directory(source_directory) if source_directory else cls.directory
        )
        target_dir = (
            get_directory(target_directory) if target_directory else cls.directory
        )
        source_glob = str(source_dir / "**" / "*.parquet")

        logging.info(f"Sinking to {target_dir} partitioned by {partition_columns}...")
        polars.scan_parquet(source_glob).sink_parquet(
            polars.PartitionBy(
                base_path=target_dir,
                key=partition_columns,
            ),
            mkdir=True,
        )
        logging.info("Repartition complete!")

    @classmethod
    def repartition_slow(
        cls,
        partition_column: str,
        partition_values: list,
        source_directory: str | Path = None,
        target_directory: str | Path = None,
    ):
        """
        Manual alternative to repartition: iterates over each
        partition value, filters the parquets, and writes a combined.parquet per chunk.
        """
        source_dir = (
            get_directory(source_directory) if source_directory else cls.directory
        )
        target_dir = (
            get_directory(target_directory) if target_directory else cls.directory
        )
        source_glob = str(source_dir / "**" / "*.parquet")

        for val in partition_values:
            output_dir = target_dir / f"{partition_column}={val}"
            output_path = output_dir / "combined.parquet"
            if output_path.exists():
                logging.info(f"Skipping {partition_column}={val} - already done.")
                continue

            output_dir.mkdir(parents=True, exist_ok=True)

            df = (
                polars.scan_parquet(source_glob)
                .filter(polars.col(partition_column) == val)
                .collect()
            )

            if len(df) == 0:
                logging.info(f"Skipping {partition_column}={val} - no rows found.")
                continue

            df.write_parquet(output_path, compression=cls.compression_mode)
            logging.info(f"Repartitioned {partition_column}={val} | Rows: {len(df):,}")

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
        from simmate.utils import get_chunk_key

        num_chunks = num_chunks or cls.num_chunks

        return df[source_column].map_elements(
            lambda x: get_chunk_key(x, num_chunks),
            return_dtype=polars.Int32,
        )

    @update_column(column_name="datastore_id")
    def add_datastore_id_column(
        cls,
        df: polars.DataFrame,
        chunk_key_column: str = "chunk_key",
    ):
        """
        Helper method to assign a unique sequential integer ID per row, offsetting
        the ID by a chunk_key multiplier. Uses update_column.
        """
        return (
            df.with_row_index("_row_idx").with_columns(
                (
                    polars.col("_row_idx").cast(polars.UInt64)
                    + polars.col(chunk_key_column).cast(polars.UInt64)
                    * polars.lit(cls.datastore_id_multiplier, dtype=polars.UInt64)
                ).alias("datastore_id")
            )
        )["datastore_id"]
