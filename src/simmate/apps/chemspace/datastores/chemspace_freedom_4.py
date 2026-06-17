# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores.base import Datastore, update_column, update_table
from simmate.utils import dispatch, get_directory, get_hash_key


class ChemspaceFreedom4(Datastore):
    """
    Datastore for processing ChemSpace Freedom 4 source data into parquets,
    building search indexes, etc.

    The full dataset is ~90 billion molecules.

    Steps to build:
        ``` python
        from simmate.apps.chemspace.datastores import ChemspaceFreedom4 as cf4
        # -----------------------------------
        cf4.convert_source_to_parquet()
        cf4.promote_staging()
        # -----------------------------------
        cf4.rename_columns({"ID": "id", "SMILES": "smiles"})
        cf4.promote_staging()
        # -----------------------------------
        cf4.add_ro5_column()
        cf4.promote_staging()
        # -----------------------------------
        cf4.add_chunk_key_column()
        cf4.promote_staging()
        # -----------------------------------
        cf4.repartition("chunk_key")
        cf4.promote_staging()
        # -----------------------------------
        cf4.add_datastore_id_column()
        cf4.promote_staging()
        # -----------------------------------
        cf4.add_fingerprints()
        cf4.promote_staging()
        # -----------------------------------
        cf4.build_usearch_index()
        ```
    """

    app_name = "chemspace"
    datastore_name = "freedom_4"

    num_chunks = 20_000
    index_batch_size = 8

    @classmethod
    def convert_source_to_parquet(cls, parallel_job: bool = False) -> Path:
        """
        Converts each .bz2 source file to a flat parquet in live_dir (1:1),
        adding a chunk_key column in this step.

        Run ChemspaceClient.download_source_data() first, then run repartition("chunk_key")
        after this completes.
        """
        source_dir = cls.base_directory / "raw"
        all_files = [p for p in source_dir.rglob("*.bz2") if p.is_file()]
        processed_hashes = {p.stem for p in cls.staging_directory.glob("*.parquet")}
        files_to_process = [
            f for f in all_files if get_hash_key(str(f)) not in processed_hashes
        ]
        logging.info(
            f"Found {len(all_files)} source files; "
            f"{len(processed_hashes)} already converted, "
            f"{len(files_to_process)} to process"
        )

        dispatch(
            files_to_process,
            cls._convert_single_source,
            parallel_job,
        )
        logging.info("Conversion complete!")

    @classmethod
    def _convert_single_source(cls, file_path: str | Path):
        file_path = Path(file_path)
        output_path = cls.staging_directory / f"{get_hash_key(str(file_path))}.parquet"
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

        df.write_parquet(output_path)
        logging.info(f"Converted {file_path.name} | Rows: {len(df):,}")

    # -------------------------------------------------------------------------
    
    # TODO: sections below should move to MoleculeDatastore class when ready
    
    @update_column("Ro5")
    def add_ro5_column(cls, df: polars.DataFrame):
        """
        Computes Ro5 from physicochemical property columns (MW, LogP, HBA, HBD).
        Ro5 is True when: MW <= 500, LogP <= 5, HBA <= 10, HBD <= 5.
        These are the classic Lipinski cutoffs.
        Requires property columns to be present in the parquet.
        """
        return df.select(
            (
                (polars.col("MW") <= 500)
                & (polars.col("LogP") <= 5)
                & (polars.col("HBA") <= 10)
                & (polars.col("HBD") <= 5)
            ).alias("Ro5")
        )["Ro5"]

    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------

    @classmethod
    def build_usearch_index(cls, parallel_job: bool = False) -> None:
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
            cls._build_usearch_index_single_batch,
            parallel_job,
        )
        logging.info("USearch index build complete!")

    @classmethod
    def _build_usearch_index_single_batch(cls, batch: list[int]):
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
