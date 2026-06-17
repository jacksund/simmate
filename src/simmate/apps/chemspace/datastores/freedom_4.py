# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores import MoleculeDatastore
from simmate.utils import dispatch, get_hash_key


class ChemspaceFreedom4(MoleculeDatastore):
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
