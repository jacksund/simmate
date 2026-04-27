# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import polars

from simmate.config import settings
from simmate.toolkit import Molecule
from simmate.toolkit.filters import RemoveInvalidSmiles
from simmate.utils import chunk_list, filter_polars_df, get_directory

from ..dataframes import MoleculeDataFrame
from ..featurizers import (
    MethodCaller,
    MorganFingerprint,
    PatternFingerprint,
    PropertyGrabber,
)
from ..featurizers.utils import load_rdkit_fingerprint_from_base64


class MoleculeStore:
    """
    This class is intended for datasets with >10 million molecules, where it
    becomes an issue to:
        1. have toolkit objects in memory all at once (memory/ram)
        2. parse all molecule inputs into objs up front (cpu time)
        3. perform substructure or similarity searches in postgres
        4. store in postgres at all ($ or disk space)

    The primary use case for this class is efficient filtering of the dataset
    via similarity, substructure, or other common properties. Many of this
    class's methods are alternative implementations of the `toolkit.filters`
    module, where the key difference is pre-caching and lazy-loading of
    molecule objects to disk.

    The class is focused only on 2D molecular formats at the moment, so
    SMILES format is required.

    We selected polars as the backend for speed and easy file chunking
    with parquet that can be used by other programs. If this class were to
    need a rewrite using another backend, alternatives to consider are
    pandas+dask, sqlite, or duckdb.
    """

    app_name: str = None
    """
    The name of the app that this datastore belongs to. This is used to
    organize datastores into subdirectories of the simmate base directory
    (e.g. ~/simmate/chembl/datastores/)
    """

    datastore_name: str
    """
    The name of the datastore. This is used to organize datastores into
    subdirectories of the simmate base directory 
    (e.g. ~/simmate/chembl/datastores/molecules)

    Use the `directory` property for the more robust Path object
    """

    # -------------------------------------------------------------------------

    chunk_size: int = 1_000_000
    """
    Number of molecule (i.e. rows) per chunked parquet file
    """

    compression_mode: str = "lz4"  # or "zstd" for slower but smaller files

    # -------------------------------------------------------------------------

    smiles_stored: str = "cleaned_only"
    # or "original_only" or "original_and_cleaned"

    metadata_columns: list[str] = []

    property_columns: list[str] = [
        "molecular_weight_exact",
        "num_atoms_heavy",
        "num_stereocenters",
        "log_p_rdkit",
        "synthetic_accessibility",
    ]

    method_columns: dict = {}  # to_inchi_key included automatically

    morgan_fingerprint_cache: bool = False

    pattern_fingerprint_cache: bool = True

    explicit_h_mode: bool = False
    """
    Whether SMILES and fingerprints should be stored with explicit hydrogens.
    This is generally needed when you want to perform many scaffold queries 
    (with R-groups), but keep in mind that this greatly increase file size
    because SMILES strings will be much larger.
    """

    # -------------------------------------------------------------------------

    @classmethod
    @property
    def directory(cls) -> Path:
        """
        Path object of the directory where all parquet chunk files are stored
        """
        # if app_name is provided, we use the <app_name>/datastores/<datastore_name>
        # otherwise we just use datastores/<datastore_name>
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
        chunk_files = [
            f
            for f in cls.directory.iterdir()
            if f.is_file() and f.suffix == ".parquet" and f.stem.isnumeric()
        ]
        return sorted(chunk_files, key=lambda f: f.stem)

    @classmethod
    @property
    def chunk_files_wildcard(cls) -> Path:
        """
        Wildcard path object for the directory + all parquet files in it.
        """
        return cls.directory / "*.parquet"

    # -------------------------------------------------------------------------

    @classmethod
    def filter_to_dataframe(
        cls,
        # note these are done *lazily* and any generated fingerprints are not
        # kept (to keep memory use low). This is counter to the MoleculeDataFrame
        # where fingerprints a kept once generated.
        similarity: Molecule = None,
        smarts: list[Molecule] = None,
        limit: int = None,
        # for the final df, whether to build out extra mol features into memory
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
        # for all stages
        parallel: bool = False,
        # then any django-like filters for columns (e.g. id__lte=100)
        **kwargs,
    ) -> MoleculeDataFrame:

        data_str = str(cls.chunk_files_wildcard)
        lazy_df = polars.scan_parquet(data_str)

        if kwargs:
            lazy_df = filter_polars_df(lazy_df, **kwargs)

        if limit:
            lazy_df = lazy_df.limit(limit)

        # execute the query (not including similarity/substructure)
        logging.info("Loading from datastore...")
        df = lazy_df.collect()

        # load_rdkit_fingerprint_from_base64
        if similarity:
            pass  # TODO
        if smarts:
            pass  # TODO

        return MoleculeDataFrame.from_polars(
            df,
            init_toolkit_objs=init_toolkit_objs,
            init_substructure_lib=init_substructure_lib,
            init_morgan_fp_lib=init_morgan_fp_lib,
            explicit_h_mode=cls.explicit_h_mode,
            parallel=parallel,
        )

    # -------------------------------------------------------------------------

    @classmethod
    def add_dataframe(
        cls,
        df: polars.DataFrame,
        parallel: bool = True,
        target_directory: str | Path = None,
    ):
        """
        Generates calculated properties+features before adding it to the disk
        store. If files are already present, the new dataframe will be appended
        to the final file + extras following the store's present chunk_size.
        """

        if "smiles" not in df.columns:
            raise Exception(
                "dataframe must have a `smiles` column to be added to MoleculeStore"
            )

        for metadata_column in cls.metadata_columns:
            if metadata_column not in df.columns:
                raise Exception(
                    f"dataframe must have a `{metadata_column}` column to be added "
                    f"to MoleculeStore. Full list of metadata columns: {cls.metadata_columns}"
                )

        output_dir = (
            get_directory(target_directory) if target_directory else cls.directory
        )
        chunk_files = sorted(
            [
                f
                for f in output_dir.iterdir()
                if f.is_file() and f.suffix == ".parquet" and f.stem.isnumeric()
            ],
            key=lambda f: f.stem,
        )
        current_chunk_index = int(chunk_files[-1].stem) + 1 if chunk_files else 0
        if chunk_files:
            logging.info(
                f"{len(chunk_files)} chunks found. New files will be appended."
            )

        for chunk in chunk_list(df, cls.chunk_size):
            chunk = cls._inflate_data_chunk(chunk, parallel=parallel)
            chunk_filename = (
                output_dir / f"{str(current_chunk_index).zfill(10)}.parquet"
            )
            chunk.write_parquet(
                chunk_filename,
                compression=cls.compression_mode,
            )
            current_chunk_index += 1

    @classmethod
    def update_row(cls, row_id, updates: dict, id_column: str = "id"):
        """
        Searches for a specific row by its ID across all chunks, applies the
        updates, and rewrites the corresponding parquet file.
        """
        for file in cls.chunk_files:
            # scan for efficiency to check if id exists
            lazy_df = polars.scan_parquet(file)
            matches = lazy_df.filter(polars.col(id_column) == row_id).collect()

            if len(matches) > 0:
                df = polars.read_parquet(file)
                # Apply updates
                for col, val in updates.items():
                    df = df.with_columns(
                        polars.when(polars.col(id_column) == row_id)
                        .then(polars.lit(val))
                        .otherwise(polars.col(col))
                        .alias(col)
                    )
                df.write_parquet(file, compression=cls.compression_mode)
                return

    @classmethod
    def update_rows_bulk(
        cls, ids_to_update: list, updates: dict, id_column: str = "id"
    ):
        """
        Iterates through all parquet files and applies updates to rows matching
        any ID in `ids_to_update`.
        """
        ids_series = polars.Series(ids_to_update)
        for file in cls.chunk_files:
            lazy_df = polars.scan_parquet(file)
            matches = lazy_df.filter(polars.col(id_column).is_in(ids_series)).collect()

            if len(matches) > 0:
                df = polars.read_parquet(file)
                for col, val in updates.items():
                    df = df.with_columns(
                        polars.when(polars.col(id_column).is_in(ids_series))
                        .then(polars.lit(val))
                        .otherwise(polars.col(col))
                        .alias(col)
                    )
                df.write_parquet(file, compression=cls.compression_mode)

    @classmethod
    def update_column(cls, column_name: str, update_method: callable):
        """
        Iterates through all rows (chunk by chunk) and applies a python callable
        to add or update a column.

        The `update_method` should accept a Polars DataFrame chunk and return
        a Polars Series or list containing the new column values.
        """
        for file in cls.chunk_files:
            df = polars.read_parquet(file)
            new_values = update_method(df)
            df = df.with_columns(polars.Series(name=column_name, values=new_values))
            df.write_parquet(file, compression=cls.compression_mode)

    @classmethod
    def reorganize_chunks(cls):
        """
        Reorganizes existing parquet files to ensure each chunk matches
        `cls.chunk_size`. Smaller chunks are combined, and larger ones are split.
        """
        # 1. Identify all current parquet files and rename them to .old
        # This handles both active files and those from a previous failed run.
        # We use .parquet.old to avoid name collisions with the new numeric files.
        for f in cls.directory.glob("*.parquet"):
            f.rename(f.parent / (f.name + ".old"))

        # 2. Gather all .old files for processing (sorted to maintain order)
        old_files = sorted(cls.directory.glob("*.parquet.old"))
        if not old_files:
            logging.info("No files found to reorganize.")
            return

        current_chunk_index = 0
        accumulated_df = None
        total_rows_read = 0
        total_rows_written = 0
        # List of (Path, end_row_index) to track when it is safe to delete .old files
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
                    cls.directory / f"{str(current_chunk_index).zfill(10)}.parquet"
                )
                chunk.write_parquet(
                    chunk_filename,
                    compression=cls.compression_mode,
                )
                current_chunk_index += 1
                total_rows_written += cls.chunk_size

                # Delete old files where ALL their rows have been written to new chunks
                while (
                    old_files_to_delete
                    and total_rows_written >= old_files_to_delete[0][1]
                ):
                    path, _ = old_files_to_delete.pop(0)
                    path.unlink()

        # 3. Write any remaining rows to the final chunk
        if accumulated_df is not None and len(accumulated_df) > 0:
            chunk_filename = (
                cls.directory / f"{str(current_chunk_index).zfill(10)}.parquet"
            )
            accumulated_df.write_parquet(
                chunk_filename,
                compression=cls.compression_mode,
            )
            total_rows_written += len(accumulated_df)

        # 4. Final cleanup of any remaining .old files
        while old_files_to_delete and total_rows_written >= old_files_to_delete[0][1]:
            path, _ = old_files_to_delete.pop(0)
            path.unlink()

    @classmethod
    def _inflate_data_chunk(
        cls,
        df: polars.DataFrame,
        parallel: bool = True,
    ) -> polars.DataFrame:

        # PERFORMANCE: For the featurization steps below, we pass the `smiles`
        # column instead of pre-initialized `Molecule` objects. Even though
        # this forces each featurizer to re-parse the SMILES, I am seeing it
        # is ~2x faster in parallel mode. This is because passing primitive
        # strings across process boundaries (IPC) is much cheaper than
        # serializing (pickling) heavy RDKit-based Molecule objects.

        logging.info("Checking for invalid molecules...")
        is_valid = RemoveInvalidSmiles.filter(
            molecules=df["smiles"].to_list(),
            return_mode="booleans",
            parallel=parallel,
        )

        num_failed = len(is_valid) - sum(is_valid)
        if num_failed > 0:
            logging.warning(f"Removed {num_failed} invalid molecules.")
            df = df.filter(is_valid)

        if cls.property_columns:
            logging.info("Calculating properties...")
            properties = PropertyGrabber.featurize_many(
                molecules=df["smiles"],
                properties=cls.property_columns,
                parallel=parallel,
                dataframe_format="polars",
            )
            df = polars.concat([df, properties], how="horizontal")
            del properties

        if cls.method_columns:
            logging.info("Calculating method-based properties...")
            extra_method_cols = {_get_smiles_with_h: {}} if cls.explicit_h_mode else {}
            method_features = MethodCaller.featurize_many(
                molecules=df["smiles"],
                method_map={
                    # Inchi key for exact-match searches
                    "to_inchi_key": {},
                    **cls.method_columns,
                    **extra_method_cols,
                },
                parallel=parallel,
                dataframe_format="polars",
            )
            if cls.explicit_h_mode:
                # because we have a new smiles column in method_features
                df = df.rename({"smiles": "smiles_original"})
                # df = df.drop("smiles")
            df = polars.concat([df, method_features], how="horizontal")
            del method_features

        # Pattern fingerprint for substructure searches
        if cls.pattern_fingerprint_cache:
            logging.info("Calculating pattern fingerprints...")
            fingerprints = PatternFingerprint.featurize_many(
                molecules=df["smiles"],
                parallel=parallel,
                vector_type="base64",
                explicit_h=cls.explicit_h_mode,
            )
            df = df.with_columns(polars.Series("pattern_fingerprint", fingerprints))
            del fingerprints

        if cls.morgan_fingerprint_cache:
            raise NotImplementedError()
            # TODO:
            # Morgan fingerprint for similirity searches
            # logging.info("Calculating morgan fingerprints...")
            # fingerprints = MorganFingerprint.featurize_many(
            #     molecules=df["smiles"],
            #     parallel=True,
            #     vector_type="base64",
            # )
            # df = df.with_columns(polars.Series("morgan_fingerprint", fingerprints))
            # del fingerprints

        return df

    # -------------------------------------------------------------------------


def _get_smiles_with_h(molecule):
    molecule.add_hydrogens()
    return molecule.to_smiles(remove_hydrogen=False)
