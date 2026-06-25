# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores.base import Datastore
from simmate.toolkit.datastores.utils import update_column, update_table
from simmate.toolkit.featurizers import (
    MethodCaller,
    PatternFingerprint,
    PropertyGrabber,
)
from simmate.utils import dispatch, get_directory


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
        smarts: list = None,
        limit: int = None,
        init_toolkit_objs: bool = False,
        init_substructure_lib: bool = False,
        init_morgan_fp_lib: bool = False,
        parallel: bool = False,
        **kwargs,
    ):
        """
        Filters the datastore and returns a MoleculeDataFrame.

        Applies column filters (django-style kwargs), an optional row limit,
        then returns the result as a MoleculeDataFrame. Similarity and SMARTS
        filtering are not yet implemented.

        Args:
            similarity: Reserved for future similarity filtering.
            smarts: Reserved for future substructure filtering.
            limit: Maximum number of rows to return. Defaults to 5_000_000.
            init_toolkit_objs: Pre-initialize RDKit Molecule objects in the MDF.
            init_substructure_lib: Pre-initialize substructure library in the MDF.
            init_morgan_fp_lib: Pre-initialize Morgan fingerprint library in the MDF.
            parallel: Use parallel processing in MoleculeDataFrame initialization.
            **kwargs: Django-style column filters (e.g. MW__lte=500).

        Returns:
            MoleculeDataFrame filtered to matching rows.
        """
        from simmate.toolkit.dataframes import MoleculeDataFrame
        from simmate.utils import filter_polars_df

        source_glob = str(cls.live_directory / "chunk_key=*" / "*.parquet")
        lazy_df = polars.scan_parquet(source_glob, hive_partitioning=True)

        if kwargs:
            lazy_df = filter_polars_df(lazy_df, **kwargs)

        if limit:
            lazy_df = lazy_df.limit(limit)

        logging.info("Loading from datastore...")
        df = lazy_df.collect()

        if similarity:
            pass  # TODO
        if smarts:
            pass  # TODO

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
        from simmate.toolkit.filters import RemoveInvalidSmiles

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

    @update_table()
    def add_fingerprints(cls, df: polars.DataFrame):
        """
        Adds MACCS, ECFP4, and FCFP4 fingerprint columns to each chunk parquet.
        Run after repartition("chunk_key") and promote_staging() have completed.
        """
        from simmate.toolkit.featurizers import USearchFingerprints

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

    index_batch_size: int = 1  # batching disabled by default

    @classmethod
    def build_fingerprint_index(cls, parallel_job: bool = False) -> None:
        """
        Builds USearch binary indexes from the chunk parquet files.

        Creates one index file per batch of chunk_keys (sized by index_batch_size)
        and writes them to datastore_dir/vectors/. Run after add_fingerprints()
        has fully completed.
        """
        vectors_dir = get_directory(cls.base_directory / "vectors")
        batches = [
            list(range(i, min(i + cls.index_batch_size, cls.num_chunks)))
            for i in range(0, cls.num_chunks, cls.index_batch_size)
        ]
        done_batches = {p.stem for p in vectors_dir.glob("maccs-*.usearch")}
        batches_to_process = [
            b for b in batches if f"maccs-{b[0]}-{b[-1]}" not in done_batches
        ]
        logging.info(
            f"{len(done_batches)} batches already done, "
            f"{len(batches_to_process)} to process"
        )
        dispatch(
            batches_to_process,
            cls._build_fingerprint_index_single_batch,
            parallel_job,
        )
        logging.info("USearch index build complete!")

    @classmethod
    def _build_fingerprint_index_single_batch(cls, batch: list[int]):
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

        live_dir = cls.live_directory
        vectors_dir = cls.base_directory / "vectors"
        source_glob = str(live_dir / "chunk_key=*" / "*.parquet")

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

        fp_type = "maccs"  # fixed for now
        cfg = fp_configs[fp_type]

        index_path = str(vectors_dir / f"{fp_type}-{batch[0]}-{batch[-1]}.usearch")
        if Path(index_path).exists():
            logging.info(f"Skipping batch {batch[0]}-{batch[-1]} - already built.")
            return

        logging.info(f"Building {fp_type} batch {batch[0]}-{batch[-1]} → {index_path}")
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

        lf = polars.scan_parquet(source_glob, hive_partitioning=True)

        for chunk_key in batch:
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
                logging.info(f"  Skipping chunk_key={chunk_key} - already indexed.")
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
                log=f"Building {fp_type} chunk {chunk_key}",
            )

            index.save(index_path)
            logging.info(f"  Saved progress | Vectors: {len(index):,}")


# needs to be top-level fxn to allow pickling
def _get_smiles_with_h(molecule):
    molecule.add_hydrogens()
    return molecule.to_smiles()
