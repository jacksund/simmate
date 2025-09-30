# -*- coding: utf-8 -*-

import logging

import polars

from simmate.utilities import chunk_list, get_directory

from ..featurizers import (
    MethodCaller,
    MorganFingerprint,
    PatternFingerprint,
    PropertyGrabber,
)


class MoleculeStore:
    """
    This class is intended to be a molecular dataset that is so large that
    it becomes an issue to:
        1. have in memory all at once
        2. parse all molecule inputs into objs up front (cpu time)
        3. perform substructure or similarity searches in postgres
        4. store in postgres at all ($ or disk space)

    We recommend using this class only if you are working with more than
    10 million molecules.

    The primary use case for this class is efficient filtering of the dataset
    via similarity, substructure, or other common properties. Many of this
    class's methods are alternative implementations of the `toolkit.filters`
    module, where the key difference is pre-caching and lazy-loading of
    molecule objects to disk.

    The class is focused only on 2D molecular formats and data at the moment, so
    SMILES format is required.
    """

    # we select polars as the backend for speed and easy file writing/chunking
    # with parquet that can be used by other programs. If this class were to
    # need a rewrite using another backend, alternatives to consider are
    # pandas+dask, sqlite, or duckdb

    # list of csv files
    # list of parquet files
    # list of smi files
    # list of sdf files

    local_path: str

    chunk_size: int = 1_000_000

    metadata_columns: list[str] = []

    property_columns: list[str] = [
        "molecular_weight_exact",
        "num_atoms_heavy",
        "num_rings",
        "log_p_rdkit",
        "synthetic_accessibility",
    ]

    method_columns: dict = {}  # to_inchi_key included automatically

    @classmethod
    @property
    def directory(cls):
        return get_directory(cls.local_path)

    @classmethod
    def add_dataframe(cls, df: polars.DataFrame):
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

        # OPTIMIZE: consider making mol objects up front, though this will
        # pose a memory issue in some cases. The current implementation below
        # is slower but more stable

        logging.info("Checking current data store chunks...")
        chunk_files = [
            f
            for f in cls.directory.iterdir()
            if f.is_file() and f.suffix == ".parquet" and f.stem.isnumeric()
        ]
        chunk_files = sorted(chunk_files, key=lambda f: f.stem)
        current_chunk_index = int(chunk_files[-1].stem) + 1 if chunk_files else 0
        if chunk_files:
            logging.info(
                f"{len(chunk_files)} chunks found. New files will be appended."
            )

        # TODO: fill last file if it is not a full size chunk or combine it
        # with list below + rebuild it by default
        total_chunks = (len(df) // cls.chunk_size) + 1 + current_chunk_index
        for chunk in chunk_list(df, cls.chunk_size):
            logging.info(f"Building chunk {current_chunk_index} of {total_chunks}...")
            chunk = cls._inflate_data_chunk(chunk)
            chunk_filename = (
                cls.directory / f"{str(current_chunk_index).zfill(10)}.parquet"
            )
            chunk.write_parquet(chunk_filename, compression="lz4")
            current_chunk_index += 1

    @classmethod
    def _inflate_data_chunk(
        cls, df: polars.DataFrame, parallel: bool = True
    ) -> polars.DataFrame:
        # General properties from Molecule obj attributes
        logging.info("Calculating properties...")
        properties = PropertyGrabber.featurize_many(
            molecules=df["smiles"],
            properties=cls.property_columns,
            parallel=parallel,
            dataframe_format="polars",
        )
        df = polars.concat([df, properties], how="horizontal")
        del properties

        # Inchi key for exact-match searches
        logging.info("Calculating method-based properties...")
        method_features = MethodCaller.featurize_many(
            molecules=df["smiles"],
            method_map={"to_inchi_key": {}, **cls.method_columns},
            parallel=parallel,
            dataframe_format="polars",
        )
        df = polars.concat([df, method_features], how="horizontal")
        del method_features

        # Pattern fingerprint for substructure searches
        logging.info("Calculating pattern fingerprints...")
        fingerprints = PatternFingerprint.featurize_many(
            molecules=df["smiles"],
            parallel=parallel,
            vector_type="base64",
        )
        df = df.with_columns(polars.Series("pattern_fingerprint", fingerprints))
        del fingerprints

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
