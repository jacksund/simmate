# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores.base import Datastore
from simmate.utils import dispatch, get_chunk_key, get_directory, get_hash_key


class ChemspaceFreedom4(Datastore):
    """
    Datastore for processing ChemSpace Freedom source data into parquets,
    building search indexes, etc.

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
        adding Ro5 and chunk_key columns in this step.

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
    def add_fingerprints(cls, parallel_job: bool = False):
        """
        adds MACCS, ECFP4, and FCFP4 fingerprint columns to each chunk's live
        parquet, writing the result as combined_w_fps.parquet alongside the
        existing combined.parquet.

        Run after repartition("chunk_key") (and promote_staging)
        has fully completed.
        """
        live_dir = cls.live_directory
        done_chunks = {
            int(p.parent.name.split("=")[1])
            for p in live_dir.rglob("combined_w_fps.parquet")
        }
        chunks_to_process = [c for c in range(cls.num_chunks) if c not in done_chunks]
        logging.info(
            f"{len(done_chunks)} chunks already done, "
            f"{len(chunks_to_process)} to process"
        )
        dispatch(
            chunks_to_process,
            cls._add_fingerprints_single_chunk,
            parallel_job,
        )
        logging.info("Fingerprint addition complete!")

    @classmethod
    def _add_fingerprints_single_chunk(cls, chunk_key: int):
        from simmate.toolkit.featurizers import USearchFingerprints

        chunk_dir = cls.live_directory / f"chunk_key={chunk_key}"
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

    # TODO: should move to MoleculeDatastore class when ready

    @classmethod
    def build_usearch_index(cls, parallel_job: bool = False) -> None:
        """
        Builds USearch binary indexes from the combined_w_fps.parquet files.

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
