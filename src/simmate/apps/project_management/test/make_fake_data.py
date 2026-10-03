# -*- coding: utf-8 -*-

"""
Generates `fake_data.zip`, which holds fake projects, tags, wallets, and
transactions for tests and for exploring the UI (see `simmate dev load-test-data`).

Rerun this script whenever the project models change. The output is
deterministic (fixed random seed), so the zip only changes when this script
does.
"""

import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from simmate.database import connect  # isort: skip

from simmate.database.utils import (  # isort: skip
    get_fake_data_path,
    get_fake_users,
    write_fake_data,
)

random.seed(1234)

REFERENCE_DATE = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
# the loader shifts all dates so that this becomes "now"

LABEL = "project_management"

# -----------------------------------------------------------------------------

users = get_fake_users()
user_ids = [u["id"] for u in users]


def days_ago(min_days: float, max_days: float) -> datetime:
    return REFERENCE_DATE - timedelta(days=random.uniform(min_days, max_days))


# -----------------------------------------------------------------------------

# (id, name, parent_id, status, discipline, description)
# fmt: off
PROJECTS = [
    (1, "Zeus", None, "Active", "Battery Materials", "Discovery of new solid-state Li-ion conductors."),
    (2, "Athena", 1, "Active", "Battery Materials", "High-throughput DFT screening of sulfide electrolytes."),
    (3, "Hermes", 1, "Active", "Battery Materials", "Synthesis and conductivity testing of top Zeus candidates."),
    (4, "Apollo", None, "Active", "Photovoltaics", "Lead-free halide perovskites for tandem solar cells."),
    (5, "Artemis", 4, "Requires Update", "Photovoltaics", "Defect tolerance of Sn-based perovskites."),
    (6, "Demeter", None, "Active", "Pesticides", "Next-generation fungicides with lower soil persistence."),
    (7, "Persephone", 6, "Under Review", "Pesticides", "Metabolite identification for lead fungicides."),
    (8, "Hephaestus", None, "Inactive", "Other", "Corrosion-resistant coatings (paused for funding)."),
    (9, "Poseidon", None, "Active", "Other", "Water purification membranes."),
    (10, "Triton", 9, "Active", "Other", None),
    (11, "Dionysus", None, "Staged for Deletion", "Other", "Duplicate project made by mistake."),
    (12, "Hestia", None, "Active", None, "Shared lab resources and equipment."),
]
# fmt: on

projects = []
children = defaultdict(list)
for project_id, name, parent_id, status, discipline, description in PROJECTS:
    created_at = days_ago(30, 400)
    projects.append(
        dict(
            id=project_id,
            created_at=created_at,
            updated_at=created_at + timedelta(days=random.uniform(0, 30)),
            name=name,
            description=description,
            status=status,
            discipline=discipline,
            parent_project_id=parent_id,
            is_top_level=parent_id is None,
        )
    )
    if parent_id:
        children[parent_id].append(project_id)


def count_children(project_id: int) -> int:
    return sum(1 + count_children(c) for c in children[project_id])


for project in projects:
    project["num_child_projects_recursive"] = count_children(project["id"])

# every project has 1-2 leaders and a few members (who aren't also leaders)
project_leaders = []
project_members = []
for project in projects:
    people = random.sample(user_ids, k=random.randint(2, 5))
    nleaders = random.randint(1, 2)
    project_leaders += [
        dict(project_id=project["id"], user_id=u) for u in people[:nleaders]
    ]
    project_members += [
        dict(project_id=project["id"], user_id=u) for u in people[nleaders:]
    ]

# -----------------------------------------------------------------------------

# (project_id, name, description) where project_id=None means all projects
TAGS = [
    (None, "high-priority", "Needs attention this quarter."),
    (None, "external", "Involves an outside collaborator."),
    (None, "needs-review", "Results should be checked before sharing."),
    (None, "published", "Results are in a published paper."),
    (2, "sulfides", "Li-P-S and Li-Sn-S chemical systems."),
    (2, "oxides", "Garnet and NASICON-type oxides."),
    (3, "ball-milled", "Samples made by mechanochemical synthesis."),
    (4, "tin-based", None),
    (6, "triazoles", None),
    (6, "field-trial", "Compounds currently in field trials."),
]

tags = []
for i, (project_id, name, description) in enumerate(TAGS, start=1):
    created_at = days_ago(10, 300)
    tags.append(
        dict(
            id=i,
            created_at=created_at,
            updated_at=created_at,
            tag_type="project-specific" if project_id else "all-projects",
            project_id=project_id,
            name=name,
            description=description,
        )
    )

# -----------------------------------------------------------------------------

# User wallets are made automatically (by a signal) when users are created,
# so they are left out here. Our ids start high to avoid theirs.
wallets = []
wallet_ids = {}  # wallet type or project id --> wallet id
for wallet_type in [
    "simmate-treasury",
    "simmate-escrow",
    "validator-pool",
    "simmate-bridge",
]:
    wallet_ids[wallet_type] = 1001 + len(wallets)
    wallets.append(
        dict(id=wallet_ids[wallet_type], wallet_type=wallet_type, project_id=None)
    )
for project in projects:
    wallet_ids[project["id"]] = 1001 + len(wallets)
    wallets.append(
        dict(
            id=wallet_ids[project["id"]],
            wallet_type="project",
            project_id=project["id"],
        )
    )
for wallet in wallets:
    wallet["created_at"] = wallet["updated_at"] = REFERENCE_DATE - timedelta(days=400)

# -----------------------------------------------------------------------------

# (transaction_type, subtype, from wallet, to wallet, uses usdc, uses tokens)
project_ids = [p["id"] for p in projects]
parent_ids = {
    p["id"]: p["parent_project_id"] for p in projects if p["parent_project_id"]
}


def random_transaction() -> tuple:
    project_id = random.choice(project_ids)
    child_id, parent_id = random.choice(list(parent_ids.items()))
    return random.choice(
        [
            ("Fund", "Stripe", "simmate-bridge", project_id, True),
            ("Fund", "Ethereum", "simmate-bridge", project_id, True),
            ("Fund", "Promotion", "simmate-treasury", project_id, True),
            ("Transfer", "Allowance Distribution", parent_id, child_id, True),
            ("Payment", "Compute Costs", project_id, "simmate-escrow", True),
            ("Payment", "Compute Costs", project_id, "simmate-escrow", True),
            ("Payment", "Compute Costs", project_id, "simmate-escrow", True),
            ("Refund", "Failed Workflow", "simmate-escrow", project_id, True),
            ("Adjust", "Add Tokens", "simmate-bridge", project_id, False),
        ]
    )


usdc_balances = defaultdict(Decimal)
token_balances = defaultdict(Decimal)
transactions = []
# dates are sorted so that balances build up in order
for created_at in sorted(days_ago(0, 120) for _ in range(180)):
    transaction_type, subtype, from_key, to_key, is_usdc = random_transaction()
    from_id = wallet_ids[from_key]
    to_id = wallet_ids[to_key]
    if is_usdc:
        amount = Decimal(random.choice([5, 10, 25, 50, 100, 250, 500]))
        # project wallets can't go negative, so we skip what they can't afford
        if from_key in project_ids and usdc_balances[from_id] < amount:
            continue
    else:
        amount = Decimal(random.choice([100, 500, 1000]))

    status = random.choices(
        ["Complete", "Pending", "Under Review", "Denied", "Failed", "Canceled"],
        weights=[85, 4, 3, 3, 3, 2],
    )[0]
    if status == "Complete":
        balances = usdc_balances if is_usdc else token_balances
        balances[from_id] -= amount
        balances[to_id] += amount

    transactions.append(
        dict(
            id=len(transactions) + 1,
            created_at=created_at,
            updated_at=created_at,
            status=status,
            transaction_type=transaction_type,
            transaction_subtype=subtype,
            sending_user_id=random.choice(user_ids),
            from_wallet_id=from_id,
            to_wallet_id=to_id,
            usdc_amount=amount if is_usdc else 0,
            token_amount=0 if is_usdc else amount,
            collateral_amount=0,
            comments=random.choice([None, None, None, "Monthly budget", "Q3 compute"]),
        )
    )

for wallet in wallets:
    wallet["usdc_balance"] = usdc_balances[wallet["id"]]
    wallet["token_balance"] = token_balances[wallet["id"]]
    wallet["collateral_balance"] = 0

# -----------------------------------------------------------------------------

write_fake_data(
    filename=get_fake_data_path(LABEL),
    tables={
        "auth.User": users,
        f"{LABEL}.Project": projects,
        f"{LABEL}.Project_leaders": project_leaders,
        f"{LABEL}.Project_members": project_members,
        f"{LABEL}.Tag": tags,
        f"{LABEL}.Wallet": wallets,
        f"{LABEL}.Transaction": transactions,
    },
    reference_date=REFERENCE_DATE,
)
