import inspect
from dataclasses import dataclass

import numpy as np
import polars

from simmate.toolkit import Molecule
from simmate.toolkit.clustering import Butina, Kmeans
from simmate.toolkit.featurizers import (
    Ecfp4Fingerprint,
    Fcfp4Fingerprint,
    MaccsFingerprint,
    MethodCaller,
    MorganFingerprint,
    PropertyGrabber,
    TopologicalFingerprint,
)
from simmate.toolkit.filters import RemoveInvalidSmiles
from simmate.toolkit.mapping import Pca, Tsne, Umap
from simmate.toolkit.similarity import Tanimoto
from simmate.toolkit.smarts_sets import CdkFunctionalGroups, ChemblAlerts

PROPERTIES = "Properties"
IDENTIFIERS = "Identifiers"
SMARTS_SETS = "SMARTS sets"
FINGERPRINTS = "Fingerprints"
CHEMICAL_SPACE = "Chemical space"
CLUSTERING = "Clustering"

# The one setting a feature can have: how many dimensions to map to, or how many
# clusters to make.
DIMS = "dims"
CLUSTERS = "clusters"

# Features that don't scale well (`Feature.slow`) ask before running on more rows
# than this.
SLOW_FEATURE_ROWS = 10_000

# `Molecule` properties that come from the file a molecule was read from (e.g. an
# SDF's title), rather than from its structure.
FILE_PROPERTIES = {"name", "comment", "num_conformers"}


@dataclass
class Feature:
    """
    One option in the Featurize panel: columns that `simmate.toolkit` computes
    from each row's molecule. See `FEATURES` and `compute_features`.
    """

    name: str  # as listed in the panel
    section: str
    key: str  # its column, or the stem of its columns' names (see `columns`)
    description: str = ""
    source: object = None
    """What computes it, by section: a `Molecule` method name (identifiers), a
    `SmartsSet.get_matches`, a `Featurizer` (fingerprints), a `ChemSpaceMapper`, or
    a `ClusteringEngine`. Properties are read by `key`."""
    setting: str | None = None  # DIMS, CLUSTERS, or None
    slow: bool = False

    def columns(self, setting: int | None = None) -> list[str]:
        """The columns it adds, given its setting (if it has one)."""
        if self.section == SMARTS_SETS:
            return [self.key, f"{self.key}_count"]
        if self.section == CHEMICAL_SPACE:
            return [f"{self.key}_{axis}" for axis in "xyz"[:setting]]
        if self.section == CLUSTERING:
            return [f"{self.key}_cluster"]
        return [self.key]


FEATURES = [
    # `Molecule` methods, called with MethodCaller
    Feature(
        "Canonical SMILES",
        IDENTIFIERS,
        "canonical_smiles",
        "RDKit's canonical SMILES",
        source="to_smiles",
    ),
    Feature(
        "Flat SMILES",
        IDENTIFIERS,
        "flat_smiles",
        "SMILES without stereochemistry",
        source="get_flattened.to_smiles",
    ),
    Feature("InChI", IDENTIFIERS, "inchi", source="to_inchi"),
    Feature("InChIKey", IDENTIFIERS, "inchi_key", source="to_inchi_key"),
    # SMARTS sets, also called with MethodCaller
    Feature(
        "ChEMBL alerts",
        SMARTS_SETS,
        "chembl_alerts",
        "The structural alerts (Glaxo, Dundee, BMS, MLSMR and PAINS) that each "
        "molecule matches, and how many",
        source=ChemblAlerts.get_matches,
    ),
    Feature(
        "CDK functional groups",
        SMARTS_SETS,
        "cdk_functional_groups",
        "The functional groups (of CDK's ~300) that each molecule has, and how many",
        source=CdkFunctionalGroups.get_matches,
    ),
    # Fingerprints, packed into bytes (as the datastores keep them)
    Feature(
        "ECFP4",
        FINGERPRINTS,
        "ecfp4",
        "2048-bit Morgan fingerprint (radius 2)",
        source=Ecfp4Fingerprint,
    ),
    Feature(
        "FCFP4",
        FINGERPRINTS,
        "fcfp4",
        "2048-bit Morgan fingerprint of atom features (radius 2)",
        source=Fcfp4Fingerprint,
    ),
    Feature(
        "MACCS keys",
        FINGERPRINTS,
        "maccs",
        "166 structural keys",
        source=MaccsFingerprint,
    ),
    Feature(
        "Topological",
        FINGERPRINTS,
        "topological",
        "RDKit's path-based fingerprint",
        source=TopologicalFingerprint,
    ),
    # Maps and clusters of Morgan fingerprints
    Feature(
        "UMAP",
        CHEMICAL_SPACE,
        "umap",
        "Maps similar molecules close together",
        source=Umap,
        setting=DIMS,
        slow=True,
    ),
    Feature(
        "PCA",
        CHEMICAL_SPACE,
        "pca",
        "The directions that vary most across the fingerprints",
        source=Pca,
        setting=DIMS,
    ),
    Feature(
        "t-SNE",
        CHEMICAL_SPACE,
        "tsne",
        "Maps similar molecules close together",
        source=Tsne,
        setting=DIMS,
        slow=True,
    ),
    Feature(
        "K-means",
        CLUSTERING,
        "kmeans",
        "Splits the molecules into a set number of clusters",
        source=Kmeans,
        setting=CLUSTERS,
    ),
    Feature(
        "Butina",
        CLUSTERING,
        "butina",
        "Groups molecules with a Tanimoto similarity of at least 0.5",
        source=Butina,
        slow=True,
    ),
    # Every `Molecule` property that gives a single value, read with PropertyGrabber
    # (listed last, as there are so many)
    *[
        Feature(name, PROPERTIES, name, inspect.getdoc(prop.fget) or "")
        for name, prop in inspect.getmembers(
            Molecule, lambda attr: isinstance(attr, property)
        )
        if prop.fget.__annotations__.get("return") in (int, float, bool, str)
        and name not in FILE_PROPERTIES
    ],
]


def compute_features(
    smiles: list[str | None],
    chosen: list[tuple[Feature, int | None]],
) -> polars.DataFrame:
    """
    Computes the columns of each chosen (feature, setting) for every row's SMILES,
    in parallel wherever the toolkit offers it. Rows whose SMILES are missing or
    can't be read get nulls.
    """
    # Only readable molecules are featurized, as one bad SMILES would fail a whole run.
    is_valid = RemoveInvalidSmiles.filter(smiles, return_mode="booleans", parallel=True)
    valid = [value for value, ok in zip(smiles, is_valid) if ok]
    if not valid:
        raise ValueError("None of the rows have a readable structure")
    results = []

    properties = [feature.key for feature, _ in chosen if feature.section == PROPERTIES]
    if properties:
        rows = PropertyGrabber.featurize_many(
            valid, properties=properties, parallel=True
        )
        results.append(
            polars.DataFrame(
                rows, schema=properties, orient="row", infer_schema_length=None
            )
        )

    # Identifiers and SMARTS sets share a single pass of MethodCaller
    calls = [
        feature
        for feature, _ in chosen
        if feature.section in (IDENTIFIERS, SMARTS_SETS)
    ]
    if calls:
        method_map = {feature.source: {} for feature in calls}
        rows = MethodCaller.featurize_many(valid, method_map=method_map, parallel=True)
        columns = {}
        for i, feature in enumerate(calls):
            values = [row[i] for row in rows]
            if feature.section == SMARTS_SETS:
                # names can contain commas, so they're joined with semicolons
                columns[feature.key] = ["; ".join(names) or None for names in values]
                columns[f"{feature.key}_count"] = [len(names) for names in values]
            else:
                columns[feature.key] = values
        results.append(polars.DataFrame(columns))

    for feature, _ in chosen:
        if feature.section == FINGERPRINTS:
            fingerprints = feature.source.featurize_many(
                valid, vector_type="numpy_packbits_bytes", parallel=True
            )
            results.append(
                polars.DataFrame(
                    {feature.key: fingerprints}, schema={feature.key: polars.Binary}
                )
            )

    # Maps and clusters all start from the same fingerprints: Morgan counts, as in
    # the toolkit's "umap-morgan" and "butina-tanimoto-morgan" presets
    grouped = [
        (feature, setting)
        for feature, setting in chosen
        if feature.section in (CHEMICAL_SPACE, CLUSTERING)
    ]
    if grouped:
        fingerprints = np.array(MorganFingerprint.featurize_many(valid, parallel=True))
    for feature, setting in grouped:
        if feature.section == CHEMICAL_SPACE:
            coordinates = feature.source.map_fingerprints(
                fingerprints, n_outputs=setting
            )
            results.append(
                polars.DataFrame(dict(zip(feature.columns(setting), coordinates)))
            )
            continue
        if feature.source is Kmeans:
            cluster_ids = Kmeans.cluster_fingerprints(
                fingerprints, n_clusters=setting, flat_output=True
            )
        else:
            cluster_ids = Butina.cluster_fingerprints(
                fingerprints, Tanimoto, flat_output=True
            )
        results.append(polars.DataFrame({feature.columns()[0]: cluster_ids}))

    # back onto every row, with nulls for the rows left out
    new = polars.concat(results, how="horizontal").with_columns(
        polars.Series("__row", np.flatnonzero(is_valid))
    )
    return (
        polars.DataFrame({"__row": np.arange(len(smiles))})
        .join(new, on="__row", how="left", maintain_order="left")
        .drop("__row")
    )
