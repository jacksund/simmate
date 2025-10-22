# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import polars

from simmate.configuration import settings
from simmate.toolkit import Molecule
from simmate.utilities import chunk_list, filter_polars_df, get_directory

from ..dataframes import MoleculeDataFrame
from ..featurizers import (
    MethodCaller,
    MorganFingerprint,
    PatternFingerprint,
    PropertyGrabber,
)
from ..featurizers.utilities import load_rdkit_fingerprint_from_base64


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

    directory_name: str
    """
    Rative path to the directory where all parquet chunk files are stored.
    These are assumed to be in the simmate base directory (~/simmate/datastores/)
    
    Use the `directory` property for the more robust Path object
    """

    chunk_size: int = 1_000_000
    """
    Number of molecule (i.e. rows) per chunked parquet file
    """

    metadata_columns: list[str] = []

    property_columns: list[str] = [
        "molecular_weight_exact",
        "num_atoms_heavy",
        "num_rings",
        "log_p_rdkit",
        "synthetic_accessibility",
    ]

    method_columns: dict = {}  # to_inchi_key included automatically

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
        return get_directory(
            settings.config_directory / "datastores" / cls.directory_name
        )

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

        chunk_files = cls.chunk_files
        current_chunk_index = int(chunk_files[-1].stem) + 1 if chunk_files else 0
        if chunk_files:
            logging.info(
                f"{len(chunk_files)} chunks found. New files will be appended."
            )

        # TODO: fill last file if it is not a full size chunk or combine it
        # with list below + rebuild it by default
        total_chunks = (len(df) // cls.chunk_size) + current_chunk_index
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
        cls,
        df: polars.DataFrame,
        parallel: bool = True,
    ) -> polars.DataFrame:
        # General properties from Molecule obj attributes
        # logging.info("Calculating properties...")
        # properties = PropertyGrabber.featurize_many(
        #     molecules=df["smiles"],
        #     properties=cls.property_columns,
        #     parallel=parallel,
        #     dataframe_format="polars",
        # )
        # df = polars.concat([df, properties], how="horizontal")
        # del properties

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
            df = df.drop("smiles")
        df = polars.concat([df, method_features], how="horizontal")
        del method_features

        # Pattern fingerprint for substructure searches
        logging.info("Calculating pattern fingerprints...")
        fingerprints = PatternFingerprint.featurize_many(
            molecules=df["smiles"],
            parallel=parallel,
            vector_type="base64",
            explicit_h=cls.explicit_h_mode,
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

    # -------------------------------------------------------------------------


def _get_smiles_with_h(molecule):
    molecule.add_hydrogens()
    return molecule.to_smiles(remove_hydrogen=False)
