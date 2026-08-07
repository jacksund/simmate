# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import polars
import pyarrow

from simmate.toolkit import Molecule
from simmate.toolkit.datastores.vector_indices import UsearchHnswIndex
from simmate.utils import chunk_list, dispatch, filter_polars_df, get_directory

from ..dataframes import MoleculeDataFrame
from ..featurizers import (
    Ecfp4Fingerprint,
    Fcfp4Fingerprint,
    MaccsFingerprint,
    MethodCaller,
    PatternFingerprint,
    PropertyGrabber,
    USearchFingerprints,
)
from ..filters import RemoveInvalidSmiles
from .base import Datastore
from .numba_funcs import tanimoto_ecfp4, tanimoto_ecfp4_1024, tanimoto_maccs
from .utils import update_column, update_table


class MoleculeDatastore(Datastore):
    """
    Base class for molecule-focused datastores. Extends Datastore with
    methods for computing molecular properties, fingerprints, and building
    similarity search indexes.
    """

    @classmethod
    def filter_to_mdf(
        cls,
        similarity=None,
        similarity_count: int = 50,
        similarity_type: str = "ecfp4",
        smarts: list = None,
        limit: int = None,
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
        parallel: bool = False,
        **kwargs,
    ) -> MoleculeDataFrame:
        """
        Filter the datastore and return a MoleculeDataFrame.

        Applies django-style column filters (``**kwargs``) and an optional row
        limit, then returns the result as a ``MoleculeDataFrame``. When
        ``similarity`` is given, runs an ANN search via the fingerprint index
        and joins a ``distance`` column (ascending) into the result.

        Args:
            similarity: Query molecule (``Molecule`` or SMILES) for similarity
                search.
            similarity_count: Number of top similar molecules to retrieve.
            similarity_type: Fingerprint type for similarity search.
                One of ``"ecfp4"``, ``"maccs"``, or ``"fcfp4"``.
            smarts: Not yet implemented — raises ``NotImplementedError``.
            limit: Maximum number of rows to return (ignored when ``similarity``
                is provided).
            init_toolkit_objs: Pre-initialize RDKit Molecule objects in the MDF.
            init_substructure_lib: Pre-initialize substructure library in the MDF.
            init_morgan_fp_lib: Pre-initialize Morgan fingerprint library in the MDF.
            parallel: Use parallel processing in MoleculeDataFrame initialization.
            **kwargs: Django-style column filters (e.g. ``MW__lte=500``).

        Returns:
            MoleculeDataFrame filtered to matching rows.
        """

        if smarts:
            raise NotImplementedError(
                "SMARTS substructure filtering is not yet implemented."
            )

        if similarity:
            sim_df = cls.search_similar(similarity, similarity_count, similarity_type)
            # cls.filter prunes the scan to the hit ids' chunk files, rather than
            # scanning every chunk in the datastore to find a handful of rows
            lazy_df = cls.filter(datastore_id__in=sim_df["datastore_id"].to_list())
        else:
            lazy_df = cls.lf

        if kwargs:
            lazy_df = filter_polars_df(lazy_df, **kwargs)
        if limit and not similarity:
            lazy_df = lazy_df.limit(limit)

        logging.info("Loading from datastore...")
        df = lazy_df.collect()
        if similarity:
            df = df.join(sim_df, on="datastore_id", how="left").sort("distance")

        return MoleculeDataFrame.from_polars(
            df,
            init_toolkit_objs=init_toolkit_objs,
            init_substructure_lib=init_substructure_lib,
            init_morgan_fp_lib=init_morgan_fp_lib,
            parallel=parallel,
        )

    # -------------------------------------------------------------------------

    # helper methods for data cleaning + populating columns

    @update_table()
    def remove_invalid_smiles(cls, df: polars.DataFrame):
        """
        Drops rows with invalid SMILES from each chunk.
        Run before any featurization steps to ensure clean input.
        """

        is_valid = RemoveInvalidSmiles.filter(
            molecules=df["smiles"].to_list(),
            return_mode="booleans",
            parallel=True,
        )
        num_failed = len(is_valid) - sum(is_valid)
        if num_failed > 0:
            logging.warning(f"Removed {num_failed} invalid molecules.")
        return df.filter(is_valid)

    @update_table()
    def add_property_columns(
        cls,
        df: polars.DataFrame,
        properties: list[str] = [
            "molecular_weight_exact",
            "num_atoms_heavy",
            "num_stereocenters",
            "num_h_acceptors",
            "num_h_donors",
            "log_p_rdkit",
            "synthetic_accessibility",
        ],
    ):
        """
        Computes physicochemical properties and adds them as columns.
        Defaults to the classic Lipinski-relevant set: MW, heavy atom count,
        stereocenters, LogP, and synthetic accessibility score.
        """
        prop_df = PropertyGrabber.featurize_many(
            molecules=df["smiles"].to_list(),
            properties=properties,
            parallel=True,
            dataframe_format="polars",
        )
        return polars.concat([df, prop_df], how="horizontal")

    @update_table()
    def add_method_columns(
        cls,
        df: polars.DataFrame,
        method_map: dict = {"to_inchi_key": {}},
    ):
        """
        Computes method-based properties and adds them as columns.
        Defaults to InChI key only. Pass a custom method_map to extend,
        e.g. {"to_inchi_key": {}, "to_smiles": {}}.
        """
        method_df = MethodCaller.featurize_many(
            molecules=df["smiles"].to_list(),
            method_map=method_map,
            parallel=True,
            dataframe_format="polars",
        )
        return polars.concat([df, method_df], how="horizontal")

    @update_column("rule_of_5")
    def add_rule_of_5_column(cls, df: polars.DataFrame):
        """
        Computes Ro5 from physicochemical property columns (MW, LogP, HBA, HBD).
        Ro5 is True when: MW <= 500, LogP <= 5, HBA <= 10, HBD <= 5.
        These are the classic Lipinski cutoffs.
        Requires property columns to be present in the parquet.
        """
        return df.select(
            (
                (polars.col("molecular_weight_exact") <= 500)
                & (polars.col("log_p_rdkit") <= 5)
                & (polars.col("num_h_acceptors") <= 10)
                & (polars.col("num_h_donors") <= 5)
            ).alias("rule_of_5")
        )["rule_of_5"]

    # -------------------------------------------------------------------------

    # for datasets that require explicit-H smiles and fps

    @update_table()
    def convert_to_explicit_h_smiles(cls, df: polars.DataFrame):

        method_df = MethodCaller.featurize_many(
            molecules=df["smiles"].to_list(),
            method_map={_get_smiles_with_h: {}},
            parallel=True,
            dataframe_format="polars",
        )
        return df.with_columns(method_df.to_series(0).alias("smiles"))

    @update_table()
    def add_pattern_fingerprint_column(
        cls, df: polars.DataFrame, explicit_h: bool = False
    ):
        """
        Adds a base64-encoded PatternFingerprint column for substructure searches.
        Run after remove_invalid_smiles() to avoid errors on bad SMILES.
        """
        fingerprints = PatternFingerprint.featurize_many(
            molecules=df["smiles"].to_list(),
            parallel=True,
            vector_type="base64",
            explicit_h=explicit_h,
        )
        return df.with_columns(polars.Series("pattern_fingerprint", fingerprints))

    # -------------------------------------------------------------------------

    # for billion-scale fingerprint similarity searches

    vector_indices: dict = {
        "maccs": UsearchHnswIndex(column_name="maccs"),
        "ecfp4": UsearchHnswIndex(column_name="ecfp4"),
        "fcfp4": UsearchHnswIndex(column_name="fcfp4"),
        "ecfp4_1024": UsearchHnswIndex(column_name="ecfp4_1024"),
        "fcfp4_1024": UsearchHnswIndex(column_name="fcfp4_1024"),
    }

    _VECTOR_CONFIGS = {
        "maccs": {
            "ndim": 168,
            "stored_bytes": 21,
            "metric_fn": tanimoto_maccs,
            "featurizer": MaccsFingerprint,
        },
        "ecfp4": {
            "ndim": 2048,
            "stored_bytes": 256,
            "metric_fn": tanimoto_ecfp4,
            "featurizer": Ecfp4Fingerprint,
        },
        "fcfp4": {
            "ndim": 2048,
            "stored_bytes": 256,
            "metric_fn": tanimoto_ecfp4,  # same 2048-bit packed layout as ecfp4
            "featurizer": Fcfp4Fingerprint,
        },
        "ecfp4_1024": {
            "ndim": 1024,
            "stored_bytes": 128,
            "metric_fn": tanimoto_ecfp4_1024,
            "featurizer": Ecfp4Fingerprint,
            "featurizer_kwargs": {"size": 1024},
        },
        "fcfp4_1024": {
            "ndim": 1024,
            "stored_bytes": 128,
            "metric_fn": tanimoto_ecfp4_1024,
            "featurizer": Fcfp4Fingerprint,
            "featurizer_kwargs": {"size": 1024},
        },
    }

    @update_table()
    def add_fingerprints(
        cls,
        df: polars.DataFrame,
        fingerprint_type: str = "usearch",
    ):
        """
        Add fingerprint column(s) to each chunk parquet.

        Note:
            For bulk dataset builds, run after ``repartition("chunk_key")``
            and ``promote_staging()`` have completed.

        Args:
            fingerprint_type: Controls which fingerprint column(s) are added.

                - ``"usearch"`` (default): Adds three packed-bit binary columns
                  (``maccs``, ``ecfp4``, ``fcfp4``) computed together in one
                  pass via ``USearchFingerprints``.
                - ``"maccs"``, ``"ecfp4"``, or ``"fcfp4"``: Adds a single
                  packed-bit binary column with that name.

        Raises:
            ValueError: If ``fingerprint_type`` is not recognized.
        """
        if fingerprint_type == "usearch":
            if len(df) == 0:
                return df.with_columns(
                    polars.Series("maccs", [], dtype=polars.Binary),
                    polars.Series("ecfp4", [], dtype=polars.Binary),
                    polars.Series("fcfp4", [], dtype=polars.Binary),
                )
            fingerprints = USearchFingerprints.featurize_many(
                df["smiles"].to_list(), parallel=True
            )
            maccs_list, ecfp4_list, fcfp4_list = zip(*fingerprints)
            return df.with_columns(
                polars.Series("maccs", list(maccs_list)),
                polars.Series("ecfp4", list(ecfp4_list)),
                polars.Series("fcfp4", list(fcfp4_list)),
            )

        elif fingerprint_type in cls._VECTOR_CONFIGS:
            if len(df) == 0:
                return df.with_columns(
                    polars.Series(fingerprint_type, [], dtype=polars.Binary)
                )
            cfg = cls._VECTOR_CONFIGS[fingerprint_type]
            fp_list = cfg["featurizer"].featurize_many(
                df["smiles"].to_list(),
                parallel=True,
                vector_type="numpy_packbits_bytes",
                **cfg.get("featurizer_kwargs", {}),
            )
            return df.with_columns(polars.Series(fingerprint_type, fp_list))

        else:
            valid = ["usearch"] + list(cls._VECTOR_CONFIGS.keys())
            raise ValueError(
                f"Unknown fingerprint_type {fingerprint_type!r}. Valid options: {valid}"
            )

    @classmethod
    def search_similar(
        cls,
        query,
        count: int = 50,
        similarity_type: str = "ecfp4",
    ) -> "polars.DataFrame":
        """
        Searches the fingerprint indexes for molecules similar to the query.

        Args:
            query: Query molecule as a ``Molecule`` object or SMILES string.
            count: Number of top results to return.
            similarity_type: Fingerprint type to use. One of ``"ecfp4"``, ``"maccs"``,
                ``"fcfp4"``, ``"ecfp4_1024"``, or ``"fcfp4_1024"``.
        """
        if isinstance(query, str):
            query = Molecule.from_smiles(query)

        cfg = cls._VECTOR_CONFIGS[similarity_type]
        fp_bytes = cfg["featurizer"].featurize(
            query,
            vector_type="numpy_packbits_bytes",
            **cfg.get("featurizer_kwargs", {}),
        )
        vec = numpy.frombuffer(fp_bytes, dtype=numpy.uint8).copy()

        index = cls.vector_indices[similarity_type]
        return index.search(cls, vec, count)

    @classmethod
    def build_fingerprint_index(
        cls,
        fp_type: str = "ecfp4",
        parallel_job: bool = False,
    ) -> None:
        """Builds similarity search indexes from the chunk parquet files."""
        index = cls.vector_indices[fp_type]
        index.build(cls, parallel_job)

    @classmethod
    def load_fingerprint_index(cls, fp_type: str = "ecfp4") -> None:
        """Loads index files for the specified fingerprint type."""
        index = cls.vector_indices[fp_type]
        index.load(cls)


# top-level (not a method) so it is picklable for multiprocessing
def _get_smiles_with_h(molecule):
    """Return SMILES with explicit hydrogens added."""
    molecule.add_hydrogens()
    return molecule.to_smiles()
