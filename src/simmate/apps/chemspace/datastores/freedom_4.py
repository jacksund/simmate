# -*- coding: utf-8 -*-

import bz2
import logging
from pathlib import Path

import polars

from simmate.toolkit.datastores import MoleculeDatastore
from simmate.toolkit.datastores.vector_indexes import FaissIvfPqIndex
from simmate.toolkit.featurizers import Ecfp4Fingerprint
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
        cf4.add_fingerprints(fingerprint_type="ecfp4_1024_faiss")
        cf4.promote_staging()
        # -----------------------------------
        cf4.build_fingerprint_index(fp_type="ecfp4_1024_faiss")
        ```
    """

    app_name = "chemspace"
    datastore_name = "freedom_4"

    num_chunks = 20_000

    vector_indexes: dict = {
        **MoleculeDatastore.vector_indexes,
        # This dataset is far too large for the HNSW graphs that the inherited
        # indexes use, so IVF+PQ is the only practical option here. With the
        # settings below, the 20,000 chunks pack into 100 shards of ~900
        # million vectors each, and at 8 bytes of PQ code + 8 bytes of id per
        # vector, that is ~1.4 TB of shards -- hence `view` mode, which maps
        # them rather than reading them in. Roughly 3.5 GB stays resident,
        # almost all of it the shards' precomputed distance tables (set
        # `skip_precompute_table` to trade search speed for that).
        #
        # TODO: search still fans out over all 100 shards, scanning
        # ~350 million codes per query (nprobe / nlist * num_vectors). Merging
        # the shards into a single on-disk index (faiss.contrib.ondisk) would
        # collapse that to one IVF traversal.
        "ecfp4_1024_faiss": FaissIvfPqIndex(
            column_name="ecfp4_1024",
            ndim=1024,
            featurizer=Ecfp4Fingerprint,
            featurizer_kwargs={"size": 1024},
            load_mode="view",
        ),
    }

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
            parallel="job" if parallel_job else "single",
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
