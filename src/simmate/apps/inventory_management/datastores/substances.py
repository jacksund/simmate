# -*- coding: utf-8 -*-

import logging

import polars

from simmate.toolkit.datastores import MoleculeDatastore


class SubstanceDatastore(MoleculeDatastore):
    """
    Datastore for the inventory_management Substance table.

    The Postgres `Substance` table links to separate `Molecule` and `Structure`
    tables via foreign keys. Here, those are flattened into a single table and
    only lightweight columns are kept (e.g. `smiles` but not `molecule`,
    `molecule_original`, `inchi`, `rdkit_mol`, `functional_groups`, etc).

    Rows come from either the Postgres table (`convert_source_to_parquet`) or
    are appended directly for massive enumerated catalogs that never live in
    Postgres (`append_rows`).

    Substances without a molecule (e.g. pure materials) have `smiles=None`, so
    do NOT run `remove_invalid_smiles`, which would drop them.

    Steps to build:
        ``` python
        from simmate.apps.inventory_management.datastores import SubstanceDatastore as sd
        # -----------------------------------
        sd.convert_source_to_parquet()
        sd.promote_staging()
        # -----------------------------------
        sd.add_chunk_key_column()
        sd.promote_staging()
        # -----------------------------------
        sd.repartition("chunk_key")
        sd.promote_staging()
        # -----------------------------------
        sd.add_datastore_id_column()
        sd.promote_staging()
        # -----------------------------------
        sd.add_property_columns()
        sd.promote_staging()
        # -----------------------------------
        sd.add_fingerprints()
        sd.promote_staging()
        # -----------------------------------
        sd.build_fingerprint_index(fp_type="ecfp4")
        ```
    """

    app_name = "inventory_management"
    datastore_name = "substances"

    num_chunks = 1_000
    # NOTE: changing this requires a full rebuild/repartition of the datastore

    source_columns: list[str] = [
        # Substance
        "id",
        "check_digit",
        "substance_type",
        "common_name",
        "iupac_name",
        "synonyms",
        "is_theoretical",
        "is_delisted",
        "is_private",
        "is_unknown",
        "is_primary",
        "is_metastable",
        "has_stereochem",
        "stereochem_type",
        "stereochem_key",
        "parent_id",
        # Substance -- molecular datasets
        "bcpc_id",
        "cas_registry_id",
        "chembl_id",
        "chemspace_id",
        "emolecules_id",
        "enamine_id",
        "pdb_id",
        "ppdb_id",
        "pubchem",
        # Substance -- crystalline datasets
        "aflow_id",
        "cod_id",
        "jarvis_id",
        "materials_project_id",
        "oqmd_id",
        # Molecule (flattened)
        "molecule__smiles",
        "molecule__inchi_key",
        # Structure (flattened)
        # TODO: move to a StructureDatastore mixin once it exists
        "structure__formula_reduced",
        "structure__chemical_system",
        "structure__spacegroup_id",
    ]
    """
    Postgres columns (as django ORM lookups) to keep in the datastore.
    Molecular properties are intentionally left out and are instead computed
    with `add_property_columns`, so that rows from Postgres and appended
    catalogs are consistent.
    """

    column_renames: dict[str, str] = {
        "molecule__smiles": "smiles",
        "molecule__inchi_key": "inchi_key",
        "structure__formula_reduced": "formula_reduced",
        "structure__chemical_system": "chemical_system",
        "structure__spacegroup_id": "spacegroup",
    }
    """
    Renames for flattened `source_columns`. All other columns keep their name.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def convert_source_to_parquet(cls):
        """
        Converts the Substance table (with its molecule/structure flattened)
        into a single parquet file in the staging directory.
        """

        from simmate.database import connect  # isort: skip

        from ..models import Substance

        df = Substance.objects.all().to_dataframe(
            columns=cls.source_columns,
            engine="polars",
        )
        df = df.rename(cls.column_renames)

        output_path = cls.staging_directory / "source.parquet"
        df.write_parquet(output_path, compression=cls.compression_mode)
        logging.info(f"Converted Substance table | Rows: {len(df):,}")

    # -------------------------------------------------------------------------

    @classmethod
    def append_rows(cls, df: polars.DataFrame):
        """
        Appends new substances directly to the live parquet chunks. This is
        intended for massive enumerated catalogs that are never added to
        Postgres.

        The input must have `id` and `smiles` columns and may only contain
        columns from `source_columns` (after `column_renames`). Property and
        fingerprint columns that exist in the live datastore are computed for
        the new rows.

        The datastore must already be partitioned by chunk_key (i.e. the full
        build steps have been run at least once). Vector indexes are NOT
        updated, so rerun `build_fingerprint_index` afterwards.
        """

        from simmate.database import connect  # isort: skip

        from ..models import Substance

        # 1. validate input
        allowed_columns = {cls.column_renames.get(c, c) for c in cls.source_columns}
        unknown_columns = set(df.columns) - allowed_columns
        if unknown_columns:
            raise ValueError(f"Unknown columns for this datastore: {unknown_columns}")
        missing_columns = {"id", "smiles"} - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        invalid_ids = [i for i in df["id"] if not Substance.validate_id(i)]
        if invalid_ids:
            raise ValueError(f"Invalid substance IDs: {invalid_ids[:10]}")
        if df["id"].n_unique() != len(df):
            raise ValueError("Duplicate IDs found in the new rows.")

        # check all chunks up front (reading only the id column) so that we
        # don't fail midway after some chunk files were already rewritten
        duplicates = cls.filter(id__in=df["id"].to_list()).select("id").collect()
        if len(duplicates) > 0:
            raise ValueError(
                f"IDs already exist in the datastore: {duplicates['id'].to_list()[:10]}"
            )

        if "check_digit" not in df.columns:
            df = df.with_columns(
                polars.col("id")
                .map_elements(Substance.calculate_check_digit, return_dtype=str)
                .alias("check_digit")
            )

        # 2. assign chunk keys
        df = cls.add_chunk_key_column(df=df)

        # 3. featurize to match the live schema
        schema = cls.schema()
        live_columns = set(schema.names())
        df = cls._featurize_new_rows(df, live_columns)

        # only keep columns that are in the live schema so that all chunk
        # files stay consistent. chunk_key is kept for grouping below
        extra_columns = set(df.columns) - live_columns - {"chunk_key"}
        if extra_columns:
            logging.warning(
                f"Dropping columns not in the live datastore: {extra_columns}"
            )
            df = df.drop(extra_columns)

        # 4. merge into each chunk file. chunk_key is dropped from each group
        # if the files don't store it (e.g. hive-partitioned)
        groups = df.partition_by(
            "chunk_key",
            as_dict=True,
            include_key="chunk_key" in live_columns,
        )
        for (chunk_key,), df_new in groups.items():
            try:
                file = cls.get_chunk_file(chunk_key)
                df_existing = polars.read_parquet(file)
            except FileNotFoundError:
                file = (
                    cls.live_directory / f"chunk_key={chunk_key}" / "combined.parquet"
                )
                file.parent.mkdir(parents=True, exist_ok=True)
                df_existing = polars.DataFrame(schema=schema)

            existing_max = df_existing["datastore_id"].max()
            if existing_max is None:
                start_id = chunk_key * cls.datastore_id_multiplier
            else:
                start_id = existing_max + 1
            df_new = df_new.with_columns(
                (polars.int_range(polars.len(), dtype=polars.UInt64) + start_id).alias(
                    "datastore_id"
                )
            )

            df_combined = polars.concat(
                [df_existing, df_new],
                how="diagonal_relaxed",
            )
            df_combined.write_parquet(file, compression=cls.compression_mode)

        logging.info(f"Appended {len(df):,} rows")
        logging.warning(
            "Vector indexes are now stale. Rerun `build_fingerprint_index` "
            "to include the new rows in similarity searches."
        )

    @classmethod
    def generate_unique_ids(cls, count: int, level: int = 2) -> list[str]:
        """
        Generates substance IDs that are not in use by either Postgres or this
        datastore. Use this when building catalogs for `append_rows`.
        """

        from simmate.database import connect  # isort: skip

        from ..models import Substance

        has_datastore = bool(cls.chunk_files)
        new_ids = set()
        while len(new_ids) < count:
            # already unique vs Postgres, so only check the datastore here
            candidates = set(Substance.generate_unique_ids(count - len(new_ids), level))
            candidates -= new_ids
            if has_datastore:
                taken = cls.filter(id__in=list(candidates)).select("id").collect()
                candidates -= set(taken["id"])
            new_ids.update(candidates)
        return list(new_ids)
