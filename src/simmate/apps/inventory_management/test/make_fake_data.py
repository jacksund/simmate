# -*- coding: utf-8 -*-

"""
Generates `fake_data.zip`, which holds fake inventory data for tests and for
exploring the UI (see `simmate dev load-test-data`).

Rerun this script whenever the inventory models change. The output is
deterministic (fixed random seed), so the zip only changes when this script
does.
"""

import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from simmate.database import connect  # isort: skip

from simmate.apps.inventory_management.models import Mixture, Substance  # isort: skip
from simmate.database.utils import (  # isort: skip
    get_fake_data_path,
    get_fake_users,
    write_fake_data,
)

random.seed(1234)

REFERENCE_DATE = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
# the loader shifts all dates so that this becomes "now"

LABEL = "inventory_management"

# -----------------------------------------------------------------------------

users = get_fake_users()
user_ids = [u["id"] for u in users]

# -----------------------------------------------------------------------------

# (id, name, storage_type, parent_id, temperature, description)
LOCATIONS = [
    (1, "Main Campus", "site", None, 20, None),
    (2, "Chemistry Building", "building", 1, 20, None),
    (3, "Materials Building", "building", 1, 20, None),
    (4, "Room 101 - Synthesis Lab", "lab", 2, 20, None),
    (5, "Room 105 - Analytical Lab", "lab", 2, 20, None),
    (6, "Room B12 - Chemical Storeroom", "room", 2, 20, "Basement, badge access"),
    (7, "Room 210 - Materials Lab", "lab", 3, 20, None),
    (8, "Fume Hood 1", "fume hood", 4, 20, None),
    (9, "Fume Hood 2", "fume hood", 4, 20, None),
    (10, "Flammables Cabinet A", "flammables cabinet", 4, 20, "Under fume hood 1"),
    (11, "Refrigerator 1", "refrigerator", 4, 4, "Explosion-proof"),
    (12, "Freezer 1", "freezer", 4, -20, None),
    (13, "Glovebox", "glovebox", 4, 20, "N2 atmosphere, <1 ppm O2"),
    (14, "Bench 3", "bench", 5, 20, None),
    (15, "Desiccator 1", "desiccator", 5, 20, None),
    (16, "Freezer 2", "freezer", 5, -80, "Ultra-low freezer"),
    (17, "Cabinet 1", "cabinet", 6, 20, None),
    (18, "Shelf 1A", "shelf", 17, 20, None),
    (19, "Shelf 1B", "shelf", 17, 20, None),
    (20, "Flammables Cabinet B", "flammables cabinet", 6, 20, None),
    (21, "Corrosives Cabinet", "cabinet", 6, 20, "Acids and bases"),
    (22, "Cold Room", "cold room", 6, 4, None),
    (23, "Cabinet 2", "cabinet", 7, 20, None),
    (24, "Shelf 2A", "shelf", 23, 20, None),
    (25, "Desiccator 2", "desiccator", 7, 20, None),
    (26, "Box 1", "box", 12, -20, "Amino acids"),
]

STORAGE = {
    # storage category --> possible location ids
    "shelf": [14, 18, 19, 24],
    "flammable": [10, 20],
    "corrosive": [21],
    "cold": [11, 22],
    "freezer": [12, 16, 26],
    "glovebox": [13],
    "desiccator": [15, 25],
}

OLD_DATE = REFERENCE_DATE - timedelta(days=900)

locations = [
    dict(
        id=id,
        name=name,
        storage_type=storage_type,
        parent_location_id=parent_id,
        temperature_celsius=temperature,
        description=description,
        created_at=OLD_DATE,
        updated_at=OLD_DATE,
    )
    for id, name, storage_type, parent_id, temperature, description in LOCATIONS
]

# -----------------------------------------------------------------------------

# fmt: off
# (key, common_name, substance_type, smiles, phase, storage, synonyms)
SUBSTANCES = [
    # solvents
    ("water", "Water", "molecule", "O", "liquid", "shelf", ["H2O", "DI water"]),
    ("meoh", "Methanol", "molecule", "CO", "liquid", "flammable", ["MeOH"]),
    ("etoh", "Ethanol", "molecule", "CCO", "liquid", "flammable", ["EtOH"]),
    ("ipa", "Isopropanol", "molecule", "CC(C)O", "liquid", "flammable", ["IPA"]),
    ("acetone", "Acetone", "molecule", "CC(C)=O", "liquid", "flammable", []),
    ("mecn", "Acetonitrile", "molecule", "CC#N", "liquid", "flammable", ["MeCN"]),
    ("dmso", "Dimethyl sulfoxide", "molecule", "CS(C)=O", "liquid", "shelf", ["DMSO"]),
    ("dmf", "N,N-Dimethylformamide", "molecule", "CN(C)C=O", "liquid", "flammable", ["DMF"]),
    ("thf", "Tetrahydrofuran", "molecule", "C1CCOC1", "liquid", "flammable", ["THF"]),
    ("dcm", "Dichloromethane", "molecule", "ClCCl", "liquid", "shelf", ["DCM"]),
    ("chcl3", "Chloroform", "molecule", "ClC(Cl)Cl", "liquid", "shelf", []),
    ("etoac", "Ethyl acetate", "molecule", "CCOC(C)=O", "liquid", "flammable", ["EtOAc"]),
    ("hexane", "Hexane", "molecule", "CCCCCC", "liquid", "flammable", ["Hexanes"]),
    ("toluene", "Toluene", "molecule", "Cc1ccccc1", "liquid", "flammable", []),
    ("ether", "Diethyl ether", "molecule", "CCOCC", "liquid", "flammable", ["Et2O"]),
    ("dioxane", "1,4-Dioxane", "molecule", "C1COCCO1", "liquid", "flammable", []),
    ("pyridine", "Pyridine", "molecule", "c1ccncc1", "liquid", "flammable", []),
    ("et3n", "Triethylamine", "molecule", "CCN(CC)CC", "liquid", "flammable", ["TEA"]),
    # acids and bases
    ("acoh", "Acetic acid", "molecule", "CC(=O)O", "liquid", "corrosive", ["AcOH"]),
    ("hcl", "Hydrochloric acid", "molecule", "Cl", "liquid", "corrosive", ["HCl"]),
    ("naoh", "Sodium hydroxide", "molecular_salt", "[Na+].[OH-]", "solid", "corrosive", ["NaOH"]),
    ("k2co3", "Potassium carbonate", "molecular_salt", "O=C([O-])[O-].[K+].[K+]", "solid", "desiccator", []),
    ("naoac", "Sodium acetate", "molecular_salt", "CC(=O)[O-].[Na+]", "solid", "shelf", ["NaOAc"]),
    # reagents
    ("ac2o", "Acetic anhydride", "molecule", "CC(=O)OC(C)=O", "liquid", "corrosive", ["Ac2O"]),
    ("benzaldehyde", "Benzaldehyde", "molecule", "O=Cc1ccccc1", "liquid", "cold", []),
    ("benzoic_acid", "Benzoic acid", "molecule", "OC(=O)c1ccccc1", "solid", "shelf", []),
    ("aniline", "Aniline", "molecule", "Nc1ccccc1", "liquid", "shelf", []),
    ("phenol", "Phenol", "molecule", "Oc1ccccc1", "solid", "shelf", []),
    ("salicylic_acid", "Salicylic acid", "molecule", "OC(=O)c1ccccc1O", "solid", "shelf", []),
    ("aspirin", "Aspirin", "molecule", "CC(=O)Oc1ccccc1C(=O)O", "solid", "shelf", ["Acetylsalicylic acid"]),
    ("caffeine", "Caffeine", "molecule", "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "solid", "shelf", []),
    ("glucose", "D-Glucose", "molecule", "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O", "solid", "shelf", ["Dextrose"]),
    ("urea", "Urea", "molecule", "NC(N)=O", "solid", "shelf", ["Carbamide"]),
    ("benzophenone", "Benzophenone", "molecule", "O=C(c1ccccc1)c1ccccc1", "solid", "shelf", []),
    ("naphthalene", "Naphthalene", "molecule", "c1ccc2ccccc2c1", "solid", "shelf", []),
    ("bromoanisole", "4-Bromoanisole", "molecule", "COc1ccc(Br)cc1", "liquid", "shelf", []),
    ("phb_oh2", "Phenylboronic acid", "molecule", "OB(O)c1ccccc1", "solid", "cold", []),
    ("methoxybiphenyl", "4-Methoxybiphenyl", "molecule", "COc1ccc(-c2ccccc2)cc1", "solid", "shelf", []),
    ("pph3", "Triphenylphosphine", "molecule", "c1ccc(P(c2ccccc2)c2ccccc2)cc1", "solid", "glovebox", ["PPh3"]),
    ("nbs", "N-Bromosuccinimide", "molecule", "O=C1CCC(=O)N1Br", "solid", "cold", ["NBS"]),
    ("ibuprofen", "Ibuprofen", "molecule", "CC(C)Cc1ccc(C(C)C(=O)O)cc1", "solid", "shelf", []),
    # stereoisomers
    ("alanine", "Alanine", "molecule", "CC(N)C(=O)O", "solid", "freezer", ["DL-Alanine"]),
    ("l_alanine", "L-Alanine", "molecule", "C[C@H](N)C(=O)O", "solid", "freezer", []),
    ("d_alanine", "D-Alanine", "molecule", "C[C@@H](N)C(=O)O", "solid", "freezer", []),
    # elements and materials
    ("cu", "Copper", "element", None, "solid", "shelf", ["Copper powder"]),
    ("fe", "Iron", "element", None, "solid", "shelf", []),
    ("zn", "Zinc", "element", None, "solid", "shelf", ["Zinc dust"]),
    ("nacl", "Sodium chloride", "material", None, "solid", "shelf", ["Table salt", "Halite"]),
    ("rutile", "Titanium dioxide (rutile)", "material", None, "solid", "shelf", ["TiO2"]),
    ("anatase", "Titanium dioxide (anatase)", "material", None, "solid", "shelf", []),
    ("silica", "Silica gel", "material", None, "solid", "shelf", ["SiO2"]),
    # special cases
    ("target", "Target compound 7", "molecule", "COc1ccc(-c2ccc(C(F)(F)F)cc2)cc1", "solid", "shelf", []),
    ("etoh_dup", None, "molecule", None, "liquid", "flammable", []),
    ("unknown", "Unknown precipitate", "other", None, "solid", "freezer", []),
]
# fmt: on

PHASES = {}  # substance/mixture key --> "solid" or "liquid"
STORAGE_OF = {}  # substance/mixture key --> STORAGE category
substance_ids = set()
while len(substance_ids) < len(SUBSTANCES):
    substance_ids.add(Substance.generate_id())
substance_ids = sorted(substance_ids)
random.shuffle(substance_ids)

molecules = []
substances = []
sub_id = {}  # key --> substance id
for (key, name, stype, smiles, phase, storage, synonyms), sid in zip(
    SUBSTANCES, substance_ids
):
    sub_id[key] = sid
    PHASES[key] = phase
    STORAGE_OF[key] = storage
    molecule_id = None
    if smiles:
        molecule_id = len(molecules) + 1
        molecules.append(
            dict(
                id=molecule_id,
                molecule=smiles,
                created_at=OLD_DATE,
                updated_at=OLD_DATE,
            )
        )
    substances.append(
        dict(
            id=sid,
            check_digit=Substance.calculate_check_digit(sid),
            substance_type=stype,
            common_name=name,
            synonyms=synonyms,
            description=None,
            molecule_id=molecule_id,
            is_primary=True,
            parent_id=None,
            is_metastable=False,
            has_stereochem=False,
            stereochem_type=None,
            is_theoretical=False,
            is_delisted=False,
            is_unknown=False,
            registered_by_id=random.choice(user_ids),
            created_at=OLD_DATE,
            updated_at=OLD_DATE,
        )
    )
sub_row = {s["id"]: s for s in substances}


def update_substance(key: str, **kwargs):
    sub_row[sub_id[key]].update(kwargs)


update_substance(
    "alanine",
    has_stereochem=True,
    stereochem_type=["constitutional"],
)
for key in ("l_alanine", "d_alanine"):
    update_substance(
        key,
        is_primary=False,
        parent_id=sub_id["alanine"],
        has_stereochem=True,
        stereochem_type=["enantiomer"],
    )
update_substance(
    "anatase", is_primary=False, parent_id=sub_id["rutile"], is_metastable=True
)
update_substance(
    "target",
    is_theoretical=True,
    description="Predicted to be a potent inhibitor. Synthesis planned.",
)
update_substance(
    "etoh_dup",
    is_delisted=True,
    is_primary=False,
    description=f"Accidental duplicate of {sub_id['etoh']}",
)
update_substance(
    "unknown",
    is_unknown=True,
    description="Unexpected precipitate from a Suzuki coupling. Awaiting NMR.",
)

# -----------------------------------------------------------------------------

# fmt: off
# (common_name, mixture_type, components, description, phase, storage)
MIXTURES = [
    ("1 M HCl (aq)", "solution", ["hcl", "water"], "1 M hydrochloric acid in water", "liquid", "corrosive"),
    ("1 M NaOH (aq)", "solution", ["naoh", "water"], "1 M sodium hydroxide in water", "liquid", "corrosive"),
    ("Brine", "solution", ["nacl", "water"], "Saturated NaCl in water", "liquid", "shelf"),
    ("3:1 MeOH:H2O", "liquid mix", ["meoh", "water"], "3:1 (v/v) methanol:water", "liquid", "flammable"),
    ("10% EtOAc/Hexanes", "liquid mix", ["etoac", "hexane"], "10% (v/v) ethyl acetate in hexanes, for TLC/columns", "liquid", "flammable"),
    ("10 mM Caffeine in DMSO", "solution", ["caffeine", "dmso"], "10 mM caffeine stock solution in DMSO", "liquid", "freezer"),
    ("TiO2 P25", "solid mix", ["anatase", "rutile"], "~80:20 anatase:rutile", "solid", "shelf"),
    ("Racemic alanine", "solid mix", ["l_alanine", "d_alanine"], "1:1 L-alanine:D-alanine", "solid", "freezer"),
]
# fmt: on

mixtures = []
mixture_components = []
for i, (name, mtype, components, description, phase, storage) in enumerate(
    MIXTURES, start=1
):
    mixtures.append(
        dict(
            id=i,
            id_prefix=Mixture.generate_id_prefix(),
            common_name=name,
            mixture_type=mtype,
            description=description,
            synonyms=[],
            created_at=OLD_DATE,
            updated_at=OLD_DATE,
        )
    )
    for key in components:
        mixture_components.append(
            dict(
                id=len(mixture_components) + 1,
                mixture_id=i,
                substance_id=sub_id[key],
            )
        )
    PHASES[f"mixture-{i}"] = phase
    STORAGE_OF[f"mixture-{i}"] = storage

# -----------------------------------------------------------------------------

SUPPLIERS = {
    "Sigma-Aldrich": "SA",
    "TCI": "T",
    "Fisher Scientific": "FS",
    "Alfa Aesar": "AA",
    "Combi-Blocks": "CB",
}

APPEARANCE = {
    "liquid": ["colorless liquid", "clear liquid", "pale yellow liquid"],
    "solid": ["white powder", "white crystalline solid", "off-white powder"],
}
APPEARANCE_OVERRIDES = {
    "cu": "reddish-brown powder",
    "fe": "dark grey powder",
    "zn": "grey powder",
    "unknown": "yellow precipitate",
    "benzaldehyde": "pale yellow liquid",
}

# amount options per phase: (units, sizes for purchased, sizes for in-house)
AMOUNTS = {
    "liquid": ("ml", [100, 250, 500, 1000, 2500], [10, 25, 50, 100]),
    "solid": ("g", [5, 10, 25, 100, 500], [0.25, 0.5, 1, 2.5, 5]),
}

CONTAINER_TYPES = {
    "liquid": ["bottle", "bottle", "flask"],
    "solid": ["vial", "jar", "bottle"],
}

batches = []
batch_lineage = []
containers = []
containers_by_batch = defaultdict(list)  # batch id --> containers
usage_logs = []
pending_usage = []  # (container, amount, date, user_id, destination_batch_id)
taken = defaultdict(Decimal)  # container id --> amount used to make other batches


def random_expiration() -> datetime | None:
    roll = random.random()
    if roll < 0.05:  # expired
        return REFERENCE_DATE - timedelta(days=random.randint(1, 60))
    elif roll < 0.11:  # expiring soon
        return REFERENCE_DATE + timedelta(days=random.randint(1, 29))
    elif roll < 0.35:  # no expiration
        return None
    return REFERENCE_DATE + timedelta(days=random.randint(45, 1000))


def add_batch(
    key: str,
    created_at: datetime,
    in_house: bool,
    parent_batches: list[dict] = [],
) -> dict:
    is_mixture = key.startswith("mixture-")
    phase = PHASES[key]
    units, purchased_sizes, in_house_sizes = AMOUNTS[phase]

    batch = dict(
        id=len(batches) + 1,
        is_mixture=is_mixture,
        substance_id=None if is_mixture else sub_id[key],
        mixture_id=int(key.split("-")[1]) if is_mixture else None,
        comments=None,
        appearance=APPEARANCE_OVERRIDES.get(key, random.choice(APPEARANCE[phase])),
        purity=round(
            random.uniform(85, 99.5) if in_house else random.uniform(95, 99.9), 1
        ),
        expiration_date=random_expiration(),
        supplier=None,
        supplier_catalog_number=None,
        supplied_by_id=random.choice(user_ids) if in_house else None,
        amount_units=units,
        created_at=created_at,
        updated_at=created_at,
        _key=key,
    )
    if is_mixture:
        batch["purity"] = None
    if not in_house:
        supplier = random.choice(list(SUPPLIERS))
        batch["supplier"] = supplier
        batch["supplier_catalog_number"] = (
            f"{SUPPLIERS[supplier]}{random.randint(10000, 999999)}"
        )
    batches.append(batch)

    # containers
    size = random.choice(in_house_sizes if in_house else purchased_sizes)
    ncontainers = random.choices([1, 2, 3, 4], weights=[45, 30, 15, 10])[0]
    for _ in range(ncontainers):
        roll = random.random()
        initial = Decimal(str(size))
        if roll < 0.10:  # used up
            current, is_depleted = Decimal(0), True
        elif roll < 0.13:  # empty but not marked as depleted yet
            current, is_depleted = Decimal(0), False
        elif roll < 0.21:  # low stock
            current, is_depleted = initial * Decimal(random.uniform(0.01, 0.09)), False
        elif roll < 0.45:  # unopened
            current, is_depleted = initial, False
        else:
            current, is_depleted = initial * Decimal(random.uniform(0.2, 0.98)), False

        location_id = random.choice(STORAGE[STORAGE_OF[key]])
        if is_depleted or random.random() < 0.03:
            location_id = None  # e.g. thrown out or misplaced

        container = dict(
            id=len(containers) + 1,
            batch_id=batch["id"],
            container_type=random.choice(CONTAINER_TYPES[phase]),
            barcode=f"C{100000 + len(containers) + 1}",
            location_id=location_id,
            comments=None,
            initial_amount=initial.quantize(Decimal("0.001")),
            current_amount=current.quantize(Decimal("0.001")),
            amount_units=units,
            is_depleted=is_depleted,
            created_at=created_at,
            updated_at=created_at,
        )
        containers.append(container)
        containers_by_batch[batch["id"]].append(container)

    # material taken from parent batches to make this one
    for parent in parent_batches:
        batch_lineage.append(
            dict(
                id=len(batch_lineage) + 1,
                from_batch_id=batch["id"],
                to_batch_id=parent["id"],
            )
        )
        source = containers_by_batch[parent["id"]][0]
        already_taken = taken[source["id"]]
        amount = (
            source["initial_amount"] * Decimal(random.uniform(0.02, 0.1))
        ).quantize(Decimal("0.001"))
        amount = min(amount, source["initial_amount"] - already_taken)
        if amount <= 0:
            continue
        source["current_amount"] = min(
            source["current_amount"],
            source["initial_amount"] - already_taken - amount,
        )
        taken[source["id"]] += amount
        pending_usage.append(
            (source, amount, created_at, batch["supplied_by_id"], batch["id"])
        )

    return batch


# purchased batches of every (non-special) substance
for key, *_ in SUBSTANCES:
    if key in ("target", "etoh_dup", "unknown", "methoxybiphenyl", "aspirin"):
        continue
    for _ in range(random.choices([1, 2, 3, 4], weights=[30, 35, 25, 10])[0]):
        created_at = REFERENCE_DATE - timedelta(days=random.randint(20, 800))
        add_batch(key, created_at, in_house=False)


def pick_batch(key: str, before: datetime) -> dict:
    options = [b for b in batches if b["_key"] == key and b["created_at"] < before] or [
        b for b in batches if b["_key"] == key
    ]
    return random.choice(options)


def add_in_house_batch(key: str, parent_keys: list[str], ndays: int = 600):
    created_at = REFERENCE_DATE - timedelta(days=random.randint(3, ndays))
    parents = [pick_batch(k, created_at) for k in parent_keys]
    created_at = max(
        [created_at] + [p["created_at"] + timedelta(days=1) for p in parents]
    )
    return add_batch(key, created_at, in_house=True, parent_batches=parents)


# in-house syntheses
for _ in range(6):
    add_in_house_batch("aspirin", ["salicylic_acid", "ac2o", "acoh"])
for _ in range(5):
    add_in_house_batch(
        "methoxybiphenyl", ["bromoanisole", "phb_oh2", "k2co3", "pph3", "dioxane"]
    )
for _ in range(3):
    add_in_house_batch("l_alanine", ["alanine"])
unknown_batch = add_in_house_batch("unknown", ["bromoanisole", "phb_oh2"], ndays=20)
unknown_batch["comments"] = "Crashed out of the reaction mixture overnight."

# in-house mixtures (prepared from the component batches)
for i, (_, _, components, *_) in enumerate(MIXTURES, start=1):
    for _ in range(random.randint(1, 3)):
        add_in_house_batch(f"mixture-{i}", components, ndays=300)

# -----------------------------------------------------------------------------

# usage logs: material removed from each container. Anything not already
# accounted for by syntheses above gets split into a few random removals
for container in containers:
    remaining = container["initial_amount"] - container["current_amount"]
    remaining -= taken[container["id"]]
    if remaining <= 0:
        continue
    npieces = random.randint(1, 4)
    cuts = sorted(random.uniform(0, 1) for _ in range(npieces - 1))
    fractions = [b - a for a, b in zip([0] + cuts, cuts + [1])]
    start = container["created_at"]
    total = remaining
    for i, fraction in enumerate(fractions):
        if i == len(fractions) - 1:  # avoid rounding drift
            amount = remaining
        else:
            amount = (total * Decimal(fraction)).quantize(Decimal("0.001"))
        if amount <= 0:
            continue
        remaining -= amount
        # skew towards recent activity
        days_ago = min(random.expovariate(1 / 25), (REFERENCE_DATE - start).days)
        date = REFERENCE_DATE - timedelta(days=days_ago, hours=random.uniform(0, 12))
        pending_usage.append((container, amount, date, random.choice(user_ids), None))

COMMENTS = [None, None, None, "For TLC", "Recrystallization", "NMR sample", "Test"]

pending_usage.sort(key=lambda u: u[2])
for container, amount, date, user_id, destination_batch_id in pending_usage:
    usage_logs.append(
        dict(
            id=len(usage_logs) + 1,
            source_container_id=container["id"],
            user_id=user_id,
            amount_removed=amount,
            comments=None if destination_batch_id else random.choice(COMMENTS),
            destination_batch_id=destination_batch_id,
            created_at=date,
            updated_at=date,
        )
    )

# -----------------------------------------------------------------------------

# cached batch columns (calculated from containers) + batch numbers
for batch in batches:
    batch_containers = containers_by_batch[batch["id"]]
    batch["num_containers"] = len(batch_containers)
    batch["total_initial_amount"] = sum(c["initial_amount"] for c in batch_containers)
    batch["total_current_amount"] = sum(c["current_amount"] for c in batch_containers)
    batch["is_depleted"] = all(c["is_depleted"] for c in batch_containers)

batch_counts = defaultdict(int)  # substance/mixture key --> batches so far
for batch in sorted(batches, key=lambda b: b["created_at"]):
    key = batch.pop("_key")
    batch_counts[key] += 1
    batch["batch_number"] = batch_counts[key]

# -----------------------------------------------------------------------------

write_fake_data(
    filename=get_fake_data_path(LABEL),
    tables={
        "auth.User": users,
        f"{LABEL}.StorageLocation": locations,
        f"{LABEL}.Molecule": molecules,
        f"{LABEL}.Substance": substances,
        f"{LABEL}.Mixture": mixtures,
        f"{LABEL}.Mixture_substances": mixture_components,
        f"{LABEL}.Batch": batches,
        f"{LABEL}.Batch_parent_batches": batch_lineage,
        f"{LABEL}.Container": containers,
        f"{LABEL}.UsageLog": usage_logs,
    },
    reference_date=REFERENCE_DATE,
)
