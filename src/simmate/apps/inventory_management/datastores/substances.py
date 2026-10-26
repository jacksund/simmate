import logging

import numpy
import polars

from simmate.toolkit import Composition, Molecule, Structure
from simmate.toolkit.datastores import MoleculeDatastore
from simmate.toolkit.featurizers import MethodCaller
from simmate.toolkit.similarity import Euclidean
from simmate.toolkit.validators.fingerprint import PartialCrystalNNFingerprint
from simmate.utils import chunk_list


class SubstanceDatastore(MoleculeDatastore):
    """
    Datastore for the inventory_management Substance table.

    The Postgres `Substance` table links to separate `Molecule` and `Structure`
    tables via foreign keys. Here, those are flattened into a single table and
    only lightweight columns are kept (e.g. `smiles` but not `molecule`,
    `molecule_original`, `inchi`, `rdkit_mol`, `functional_groups`, etc).

    This datastore holds the full catalog of substances, while Postgres only
    holds "hot" ones (level 1, those linked to by other tables, and those
    recently looked up). Rows get here in two ways:

    - massive catalogs are registered with `get_or_create_ids` using
      `write_to="datastore"`, and never reach Postgres
    - substances registered in Postgres (e.g. via the website) are copied
      over by `compact`, which then removes unused level 2/3 substances from
      Postgres

    All registration goes through `get_or_create_ids`, so both paths use the
    same uniqueness checks.

    Substances without a molecule (e.g. pure materials) have `smiles=None`, so
    do NOT run `remove_invalid_smiles`, which would drop them.

    Steps for a one-time setup from an existing Postgres table (afterwards,
    just run `sd.compact()` periodically):
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
        "replaced_by_id",
        "is_private",
        "is_unknown",
        "is_primary",
        "is_metastable",
        "has_stereochem",
        "stereochem_type",
        "stereochem_key",
        "parent_id",
        # Molecule (flattened)
        "molecule__smiles",
        "molecule__inchi_key",
        # Structure (flattened)
        # TODO: move to a StructureDatastore mixin once it exists
        "structure__structure",
        "structure__formula_reduced",
        "structure__chemical_system",
        "structure__spacegroup_id",
    ]
    """
    Postgres columns (as django ORM lookups) to keep in the datastore.
    Molecular properties are intentionally left out and are instead computed
    with `add_property_columns`, so that rows from Postgres and appended
    catalogs are consistent.

    NOTE: rows are written with only the columns that are already in the live
    datastore, so adding a column here requires a rebuild (see the class
    docstring).
    """

    column_renames: dict[str, str] = {
        "molecule__smiles": "smiles",
        "molecule__inchi_key": "inchi_key",
        "structure__structure": "structure",
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

        from simmate.database import connect  # ruff: isort: skip

        from ..models import Substance

        df = Substance.objects.to_dataframe(
            columns=cls.source_columns,
            engine="polars",
        )
        df = df.rename(cls.column_renames)

        output_path = cls.staging_directory / "source.parquet"
        df.write_parquet(output_path, compression=cls.compression_mode)
        logging.info(f"Converted Substance table | Rows: {len(df):,}")

    # -------------------------------------------------------------------------

    # REGISTRATION

    # Every substance is registered through `get_or_create_ids`, which decides
    # whether each entry is new or already registered (in either Postgres or
    # this datastore) and links new substances to their parents (e.g. the flat
    # version of a stereoisomer). Postgres wins for any ID that it has, as it
    # is always the newer copy. Third-party tables (e.g. `PdbLigand`) are
    # linked to their substances with `link_table`.
    #
    # NOTE: writes are assumed to come from a single process at a time, so
    # there is no locking between checking for and creating new substances.
    #
    # TODO: lookups by InChI key and formula scan the entire datastore. This
    # is fine for now, but will eventually need an index. Postgres could also
    # do a fast precheck, so that the scan is skipped when every entry is
    # found there.

    structure_match_tolerance: float = 0.9
    """
    The maximum distance between the PartialCrystalNN fingerprints of two
    crystal structures (with the same reduced formula) for them to be
    considered the same substance.

    TODO: this is the default of `PartialCrystalNNFingerprint` and has not
    been tuned for duplicate detection yet (e.g. with known duplicates
    between the Materials Project and OQMD).
    """

    @classmethod
    def get_or_create_id(
        cls,
        molecule: Molecule | str = None,
        structure: Structure = None,
        level: int = 1,
        write_to: str = "postgres",
        **columns,
    ) -> str:
        """
        Registers a single substance and gives its ID. See `get_or_create_ids`
        for details.
        """
        return cls.get_or_create_ids(
            [dict(molecule=molecule, structure=structure, **columns)],
            level=level,
            write_to=write_to,
        )[0]

    @classmethod
    def get_or_create_ids(
        cls,
        entries: list[dict],
        level: int = 1,
        write_to: str = "postgres",
    ) -> list[str]:
        """
        Registers many substances at once and gives the substance ID of each
        entry (in the same order). This is the single entry point for
        registering substances.

        Each entry is a dictionary with a `molecule` (a toolkit `Molecule`, a
        str such as an SDF or SMILES, or None), a crystal `structure` (a
        toolkit `Structure` or anything that `Structure.from_dynamic` accepts,
        or None), plus any extra columns to set if a new substance is made
        (e.g. `registered_by_id`).

        - Entries that are already registered give the existing substance ID.
          The existing substance is left unchanged. See `_find_match` for the
          uniqueness checks.
        - New entries get a new substance with an ID of the given `level`.
          Repeated entries share one new substance.
        - New substances are linked to their parent (e.g. the flat version of
          a stereoisomer), which is registered first if needed.
        - Entries with neither a molecule nor a structure are registered as
          unknown substances (`is_unknown=True`). These are never matched and
          always get a new level 3 ID.

        Args:
            entries: The substances to register.
            level: The ID level to give new substances.
            write_to: Where new substances are saved. Either "postgres" (the
                default) or "datastore". Use "datastore" for massive catalogs
                (e.g. billions of enumerated molecules) that should never be
                added to Postgres, and only run it from a single offline
                process. Vector indexes are NOT updated in this case, so rerun
                `build_fingerprint_index` afterwards.

        Returns:
            The substance ID of each entry.
        """

        from simmate.database import connect  # ruff: isort: skip

        from django.db import transaction

        from ..models import Structure as DatabaseStructure
        from ..models import Substance

        if write_to not in ("postgres", "datastore"):
            raise ValueError(f"Unknown write_to option: {write_to}")

        # make sure extra columns aren't included by accident
        if write_to == "datastore":
            allowed_columns = {cls.column_renames.get(c, c) for c in cls.source_columns}
            unknown_columns = {c for entry in entries for c in entry} - (
                allowed_columns - {"id", "check_digit"} | {"molecule", "structure"}
            )
            if unknown_columns:
                raise ValueError(
                    f"Unknown columns for this datastore: {unknown_columns}"
                )

        # NOTE: This code would be a lot easier to read if this was done
        # as a for-loop over each entry, but we gain massive speedups by
        # doing things in parallel / as lists.
        with transaction.atomic():
            # 1. NORMALIZE. Each entry gets an `info` dict with the details
            # used for matching, which can involve molecular and/or crystal feats
            molecule_features = MethodCaller.featurize_many(
                molecules=[entry.get("molecule") for entry in entries],
                method_map={
                    "to_smiles": {},
                    "to_inchi_key": {},
                    "get_flattened.to_smiles": {},
                },
                parallel=len(entries) >= 10_000,
            )
            # Crystal structures are saved as their primitive cell, so that all
            # substances use the same cell convention.
            structures = [
                (
                    Structure.from_dynamic(entry["structure"]).get_primitive_structure()
                    if entry.get("structure") is not None
                    else None
                )
                for entry in entries
            ]
            fingerprints = cls._get_fingerprints(structures)
            # now bring the data together into a final dict
            infos = []
            for features, structure, fingerprint in zip(
                molecule_features, structures, fingerprints
            ):
                smiles, inchi_key, flat_smiles = (
                    features if features is not None else (None, None, None)
                )
                infos.append(
                    dict(
                        has_molecule=features is not None,
                        has_structure=structure is not None,
                        smiles=smiles,
                        inchi_key=inchi_key or None,  # None when InChI fails
                        # None when the molecule has no stereochemistry
                        flat_smiles=flat_smiles if flat_smiles != smiles else None,
                        structure=structure,
                        formula=(
                            structure.composition.reduced_formula
                            if structure is not None
                            else None
                        ),
                        fingerprint=fingerprint,
                    )
                )

            # 2. PARENTS. Each entry has at most one parent:
            #   - a phase of a compound (molecule + structure) --> the molecule
            #     (e.g. an aspirin crystal --> aspirin)
            #   - a stereoisomer --> its flat version (stereochem removed)
            #     (e.g. (R)-ibuprofen --> ibuprofen)
            # Parents are registered through this same method, so a crystal of
            # a stereoisomer recurses twice (crystal --> stereoisomer --> flat).
            #
            # TODO: molecular salts --> the salt-free molecule (e.g. with
            # `Molecule.largest_component`)
            # TODO: crystal structures --> the primary (e.g. most stable) phase
            # of the same composition
            parent_entries = {}  # entry index --> parent entry
            for index, info in enumerate(infos):
                if info["has_molecule"] and info["has_structure"]:
                    parent_entries[index] = dict(molecule=entries[index]["molecule"])
                elif info["flat_smiles"]:
                    parent_entries[index] = dict(molecule=info["flat_smiles"])
            parent_ids = {}  # entry index --> parent substance id
            if parent_entries:
                parent_ids = dict(
                    zip(
                        parent_entries,
                        cls.get_or_create_ids(
                            list(parent_entries.values()),
                            level=level,
                            write_to=write_to,
                        ),
                    )
                )

            # 3. CANDIDATES. All registered substances that could match any
            # entry are loaded at once, as each lookup scans the full datastore.
            candidates = cls._get_candidates(
                inchi_keys={info["inchi_key"] for info in infos} - {None},
                formulas={info["formula"] for info in infos} - {None},
            )

            # 4. MATCH each entry. New entries are given a placeholder ID and
            # added to the candidates, so that repeated entries match them.
            substance_ids = []
            new_entries = {}  # placeholder id --> entry index
            for index, info in enumerate(infos):
                substance_id = cls._find_match(info, candidates)
                if not substance_id:
                    substance_id = f"new-{index}"
                    new_entries[substance_id] = index
                    candidate = dict(
                        id=substance_id,
                        inchi_key=info["inchi_key"],
                        formula=info["formula"],
                        has_structure=info["has_structure"],
                        fingerprint=info["fingerprint"],
                    )
                    cls._add_candidate(candidates, candidate)
                substance_ids.append(substance_id)

            # 5. IDs for the new substances. Unknowns always get a level 3 ID.
            levels = {
                placeholder: (
                    level
                    if infos[index]["has_molecule"] or infos[index]["has_structure"]
                    else 3
                )
                for placeholder, index in new_entries.items()
            }
            new_ids = {}
            for id_level in set(levels.values()):
                placeholders = [p for p, lvl in levels.items() if lvl == id_level]
                new_ids |= dict(
                    zip(
                        placeholders,
                        cls.generate_unique_ids(len(placeholders), id_level),
                    )
                )
            substance_ids = [new_ids.get(i, i) for i in substance_ids]

            # 6. WRITE the new substances, using the first entry given for
            # each. Extra columns given in an entry take priority over these
            # defaults.
            new_rows = []  # (columns, entry index)
            for placeholder, index in new_entries.items():
                info = infos[index]
                substance_id = new_ids[placeholder]
                columns = dict(
                    id=substance_id,
                    check_digit=Substance.calculate_check_digit(substance_id),
                    substance_type=(
                        "molecule"
                        if info["has_molecule"]
                        else "material"
                        if info["has_structure"]
                        else None
                    ),
                    is_unknown=not info["has_molecule"] and not info["has_structure"],
                    parent_id=parent_ids.get(index),
                )
                columns.update(
                    {
                        k: v
                        for k, v in entries[index].items()
                        if k not in ("molecule", "structure")
                    }
                )
                new_rows.append((columns, index))

            if write_to == "postgres":
                # existing substances that are only in the datastore are copied
                # over, so that they can be linked to right away (e.g. by a
                # new batch)
                Substance._hydrate(list(set(substance_ids) - set(new_ids.values())))
                Substance._bulk_create_rows(
                    [
                        columns
                        | dict(
                            molecule=entries[index].get("molecule"),
                            inchi_key=infos[index]["inchi_key"],
                            structure=infos[index]["structure"],
                        )
                        for columns, index in new_rows
                    ]
                )

            elif write_to == "datastore" and new_rows:
                rows = []
                for columns, index in new_rows:
                    info = infos[index]
                    row = columns | dict(
                        smiles=info["smiles"],
                        inchi_key=info["inchi_key"],
                    )
                    if info["has_structure"]:
                        structure = DatabaseStructure.from_toolkit(
                            structure=info["structure"],
                            as_dict=True,
                        )
                        row |= {
                            new: structure[old.removeprefix("structure__")]
                            for old, new in cls.column_renames.items()
                            if old.startswith("structure__")
                        }
                    rows.append(row)
                cls.upsert_rows(polars.DataFrame(rows, infer_schema_length=None))
                logging.warning(
                    "Vector indexes are now stale. Rerun `build_fingerprint_index` "
                    "to include the new rows in similarity searches."
                )

        logging.info(f"Registered {len(new_rows):,} new substances")
        return substance_ids

    @classmethod
    def link_table(cls, table, level: int = 1, batch_size: int = 10_000):
        """
        Registers every entry of a third-party table (e.g. `PdbLigand` or
        `CodStructure`) that is not linked yet (see `get_or_create_ids`) and
        sets its `substance` column.

        The table must have either a molecule or crystal structure column,
        which is found from its base class. Entries without a valid molecule
        or structure are skipped. Only unlinked entries are loaded, so this
        can be rerun after new entries are added.

        Args:
            table: The database table to link. It must have a `substance`
                foreign key.
            level: The ID level to give new substances.
            batch_size: The number of entries to register at a time.
        """

        from simmate.database import connect  # ruff: isort: skip

        from django.db.models import Q

        from simmate.apps.rdkit.models import Molecule as MoleculeTable
        from simmate.database.mixins.structure import Structure as StructureTable

        entries = table.objects.filter(substance__isnull=True)
        if issubclass(table, MoleculeTable):
            # Molecules without an InChI key can never be matched, so would
            # give a new substance every time they are registered. RDKit gives
            # an empty key when InChI fails (e.g. for dative bonds to metals or
            # `*` dummy atoms).
            # TODO: match these on canonical SMILES instead
            column = "molecule"
            entries = entries.filter(molecule__isnull=False).exclude(
                Q(inchi_key__isnull=True) | Q(inchi_key="")
            )
        elif issubclass(table, StructureTable):
            column = "structure"
            entries = entries.filter(structure__isnull=False).exclude(
                is_invalid_structure=True
            )
        else:
            raise TypeError(f"{table.table_name} has no molecule or structure")

        # TODO: address extremely large tables where this call will fail (e.g.
        # Enamine and Chemspace), which will need a variant that is given a
        # datastore instead of a table.
        entries = list(entries.values_list("id", column))
        for batch in chunk_list(entries, batch_size):
            substance_ids = cls.get_or_create_ids(
                [
                    (
                        dict(molecule=value)
                        if column == "molecule"
                        else dict(structure=Structure.from_database_string(value))
                    )
                    for _, value in batch
                ],
                level=level,
            )
            table.objects.bulk_update(
                [
                    table(id=entry_id, substance_id=substance_id)
                    for (entry_id, _), substance_id in zip(batch, substance_ids)
                ],
                fields=["substance"],
                batch_size=batch_size,
            )
            logging.info(f"Linked {len(batch):,} {table.table_name} entries")

    @classmethod
    def _get_candidates(
        cls,
        inchi_keys: set[str],
        formulas: set[str],
    ) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
        """
        Gives every registered (and not delisted) substance that has one of
        the given InChI keys or reduced formulas, from both Postgres and the
        datastore. Postgres substances come first (oldest first), followed by
        those only in the datastore.

        Returns:
            The candidates grouped by InChI key and by reduced formula. Each
            candidate is a dict with its `id`, `inchi_key`, `formula`,
            `has_structure`, and `fingerprint` (crystal structures only).
        """
        from ..models import Substance

        rows = {}  # substance id --> (id, inchi key, formula, structure str)
        for lookup, values in (
            ("molecule__inchi_key__in", inchi_keys),
            ("structure__formula_reduced__in", formulas),
        ):
            for batch in chunk_list(list(values), 10_000):
                for row in (
                    Substance.objects.filter(**{lookup: batch})
                    .exclude(is_delisted=True)
                    .order_by("created_at")
                    .values_list(
                        "id",
                        "molecule__inchi_key",
                        "structure__formula_reduced",
                        "structure__structure",
                    )
                ):
                    rows.setdefault(row[0], row)

        if (inchi_keys or formulas) and cls.chunk_files:
            # the structure column is missing in datastores built before
            # crystal structures were supported
            columns = ["id", "inchi_key", "formula_reduced", "structure"]
            columns = [c for c in columns if c in cls.schema().names()]
            df = (
                cls.lf.filter(
                    (
                        polars.col("inchi_key").is_in(list(inchi_keys))
                        | polars.col("formula_reduced").is_in(list(formulas))
                    )
                    & ~polars.col("is_delisted").fill_null(False)
                )
                .select(columns)
                .collect()
            )
            # IDs in Postgres were already checked above, and their datastore
            # copy may be outdated (e.g. since delisted)
            in_postgres = cls.get_postgres_ids(df["id"].to_list())
            for row in df.iter_rows(named=True):
                if row["id"] not in in_postgres:
                    rows.setdefault(
                        row["id"],
                        (
                            row["id"],
                            row["inchi_key"],
                            row["formula_reduced"],
                            row.get("structure"),
                        ),
                    )

        structures = {
            substance_id: Structure.from_database_string(structure)
            for substance_id, _, _, structure in rows.values()
            if structure
        }
        fingerprints = dict(
            zip(structures, cls._get_fingerprints(list(structures.values())))
        )

        candidates = ({}, {})
        for substance_id, inchi_key, formula, structure in rows.values():
            candidate = dict(
                id=substance_id,
                inchi_key=inchi_key,
                formula=formula,
                has_structure=structure is not None,
                fingerprint=fingerprints.get(substance_id),
            )
            cls._add_candidate(candidates, candidate)
        return candidates

    @staticmethod
    def _add_candidate(
        candidates: tuple[dict[str, list[dict]], dict[str, list[dict]]],
        candidate: dict,
    ):
        """
        Adds a candidate (see `_get_candidates`) to the InChI key and reduced
        formula groups, in place.
        """
        by_inchi_key, by_formula = candidates
        if candidate["inchi_key"]:
            by_inchi_key.setdefault(candidate["inchi_key"], []).append(candidate)
        if candidate["formula"]:
            by_formula.setdefault(candidate["formula"], []).append(candidate)

    @classmethod
    def _find_match(
        cls,
        info: dict,
        candidates: tuple[dict[str, list[dict]], dict[str, list[dict]]],
    ) -> str | None:
        """
        The uniqueness checks for a single entry. Gives the ID of the first
        candidate that is the same substance, or None if the entry is new.

        Args:
            info: The normalized entry (see step 1 of `get_or_create_ids`).
            candidates: The output of `_get_candidates`.
        """
        by_inchi_key, by_formula = candidates
        inchi_key = info["inchi_key"]

        # a. MOLECULE ONLY: the substance with the same InChI key and no
        # crystal structure.
        # TODO: an InChI key match does not always mean a substance match,
        # such as with atropisomers or true InChI key clashes (which become
        # possible in very large datasets, e.g. >1 trillion entries). These
        # will need extra checks, such as with `stereochem_key` and the
        # other stereochem flags.
        if info["has_molecule"] and not info["has_structure"]:
            if not inchi_key:
                return None  # can't be matched (e.g. InChI failed)
            for candidate in by_inchi_key.get(inchi_key, []):
                if not candidate["has_structure"]:
                    return candidate["id"]
            return None

        # b. CRYSTAL STRUCTURE ONLY: a material with the same reduced formula
        # and a similar fingerprint. Fingerprints use per-site stats, so they
        # don't depend on the cell size, and no filter on the number of
        # sites is needed.
        if info["has_structure"] and not info["has_molecule"]:
            if info["fingerprint"] is None:
                return None  # can't be matched (e.g. disordered structure)
            for candidate in by_formula.get(info["formula"], []):
                if (
                    not candidate["inchi_key"]
                    and candidate["fingerprint"] is not None
                    and Euclidean.is_match(
                        info["fingerprint"],
                        candidate["fingerprint"],
                        cutoff=cls.structure_match_tolerance,
                    )
                ):
                    return candidate["id"]
            return None

        # c. MOLECULE + CRYSTAL STRUCTURE: a phase of a compound (e.g. a
        # polymorph of a molecular crystal). Matches a phase of the same
        # molecule with a similar fingerprint.
        if info["has_molecule"] and info["has_structure"]:
            if not inchi_key or info["fingerprint"] is None:
                return None
            for candidate in by_inchi_key.get(inchi_key, []):
                if (
                    candidate["has_structure"]
                    and candidate["fingerprint"] is not None
                    and Euclidean.is_match(
                        info["fingerprint"],
                        candidate["fingerprint"],
                        cutoff=cls.structure_match_tolerance,
                    )
                ):
                    return candidate["id"]
            return None

        # d. NEITHER: unknown substances are never matched
        return None

    @staticmethod
    def _get_fingerprints(
        structures: list[Structure | None],
    ) -> list[numpy.ndarray | None]:
        """
        Gives the PartialCrystalNN fingerprint of each structure (see
        `Structure.get_fingerprint`), or None where it fails (e.g. for
        disordered structures) or where the structure is None.

        Structures are featurized in one batch per reduced formula, as the
        featurizer depends on the elements. Large batches are run in parallel.
        """
        indexes_by_formula = {}
        for index, structure in enumerate(structures):
            if structure is None:
                continue
            formula = structure.composition.reduced_formula
            indexes_by_formula.setdefault(formula, []).append(index)

        fingerprints = [None] * len(structures)
        for formula, indexes in indexes_by_formula.items():
            # elements are given in a fixed order (that of the reduced
            # formula), so that fingerprints of the same composition can be
            # compared
            featurizer = PartialCrystalNNFingerprint.get_featurizer(
                composition=Composition(formula)
            )
            # starting a process pool is only worth it for many structures
            if len(indexes) < 100:
                featurizer.set_n_jobs(1)
            features = featurizer.featurize_many(
                [structures[index] for index in indexes],
                ignore_errors=True,  # failures give NaN values
                pbar=False,
            )
            for index, feature in zip(indexes, features):
                feature = numpy.array(feature, dtype=float)
                if numpy.isnan(feature).any():
                    logging.warning(
                        f"Fingerprint failed for {formula}. "
                        "It will be treated as a unique structure."
                    )
                    continue
                fingerprints[index] = feature
        return fingerprints

    @classmethod
    def get_postgres_ids(cls, ids: list[str]) -> set[str]:
        """
        Gives which of the IDs are in the Postgres table.
        """
        from ..models import Substance

        found = set()
        for batch in chunk_list(ids, 10_000):
            found.update(
                Substance.objects.filter(id__in=batch).values_list("id", flat=True)
            )
        return found

    @classmethod
    def generate_unique_ids(cls, count: int, level: int = 1) -> list[str]:
        """
        Generates IDs at the given level that are not in use (in either
        Postgres or the datastore) and are unique amongst themselves.
        """
        from ..models import Substance

        has_datastore = bool(cls.chunk_files)
        new_ids = set()
        while len(new_ids) < count:
            num_needed = count - len(new_ids)
            candidates = {Substance.generate_id(level) for _ in range(num_needed)}
            candidates -= new_ids
            candidates -= cls.get_postgres_ids(list(candidates))
            if has_datastore:
                taken = cls.filter(id__in=list(candidates)).select("id").collect()
                candidates -= set(taken["id"])
            new_ids.update(candidates)
        return list(new_ids)

    # -------------------------------------------------------------------------

    @classmethod
    def compact(cls, evict: bool = True):
        """
        Brings the datastore up to date with Postgres, and should be run
        periodically (e.g. nightly).

        1. Copies new + changed Postgres substances into the datastore.
        2. Evicts level 2/3 substances from Postgres that are synced and that
           nothing links to. These stay available through the datastore.

        Vector indexes are NOT updated, so rerun `build_fingerprint_index`
        afterwards.

        Args:
            evict: Whether to run step 2.
        """

        from simmate.database import connect  # ruff: isort: skip

        from django.db.models import F, Q
        from django.utils import timezone

        from ..models import Molecule as DatabaseMolecule
        from ..models import Substance

        # 1. flush. We only mark entries as synced if they haven't changed
        # since we started (e.g. via a website form)
        synced_at = timezone.now()
        dirty = Substance.objects.filter(
            Q(datastore_synced_at__isnull=True)
            | Q(updated_at__gt=F("datastore_synced_at")),
            updated_at__lte=synced_at,
        )
        # all rows are written at once so that each chunk file is only
        # rewritten once
        df = dirty.to_dataframe(columns=cls.source_columns, engine="polars")
        cls.upsert_rows(df.rename(cls.column_renames))
        dirty.update(datastore_synced_at=synced_at)
        logging.info(f"Flushed {len(df):,} substances from Postgres")

        # 2. evict
        if not evict:
            return
        candidates = [
            (substance_id, molecule_id)
            for substance_id, molecule_id in Substance.objects.filter(
                datastore_synced_at__isnull=False,
                updated_at__lte=F("datastore_synced_at"),
            ).values_list("id", "molecule_id")
            if Substance.get_id_level(substance_id) in (2, 3)
        ]
        num_evicted = 0
        for batch in chunk_list(candidates, 10_000):
            molecule_ids = dict(batch)  # substance id --> molecule id
            evict_ids = set(molecule_ids) - Substance.get_referenced_ids(
                list(molecule_ids)
            )
            Substance.objects.filter(id__in=evict_ids).delete()
            DatabaseMolecule.objects.filter(
                id__in=[molecule_ids[i] for i in evict_ids if molecule_ids[i]],
                substances__isnull=True,
            ).delete()
            num_evicted += len(evict_ids)
        logging.info(f"Evicted {num_evicted:,} substances from Postgres")
