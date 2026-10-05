"""A random compound-registry style dataset: several chemical series with random assay results."""

import datetime

import numpy as np
import polars

from simmate.toolkit import Molecule
from simmate.toolkit.dataframes import MoleculeDataFrame

# Each scaffold has two substitution sites; "({R1})" / "({R2})" are dropped entirely for H.
SCAFFOLDS = {
    "Benzamide": "O=C(N({R2}))c1ccc({R1})cc1",
    "Sulfonamide": "O=S(=O)(N({R2}))c1ccc({R1})cc1",
    "Aminopyrimidine": "c1cc({R1})nc(N({R2}))n1",
    "Arylpiperazine": "c1cc({R1})ccc1N1CCN({R2})CC1",
    "Indole acetamide": "c1cc({R1})c2c(c1)c(CC(=O)N({R2}))c[nH]2",
    "Aminoquinoline": "c1ccc2ncc({R1})c(N({R2}))c2c1",
}
R1_GROUPS = ["", "F", "Cl", "Br", "C", "OC", "C(F)(F)F", "C#N", "O", "N", "S(C)(=O)=O"]
# R-group rings use ring-closure digit 9 so they can't collide with the scaffold's open rings.
R2_GROUPS = [
    "",
    "C",
    "CC",
    "C(C)C",
    "C9CC9",
    "c9ccccc9",
    "Cc9ccccc9",
    "CCO",
    "CCN(C)C",
    "C9CCOCC9",
    "c9ccncc9",
    "CC(=O)O",
]


def _fill(template: str, r1: str, r2: str) -> str:
    for name, group in [("R1", r1), ("R2", r2)]:
        template = template.replace(f"({{{name}}})", f"({group})" if group else "")
    return template


def build_dataset(n=400, seed=42) -> MoleculeDataFrame:
    rng = np.random.default_rng(seed)
    combos = [
        (series, r1, r2) for series in SCAFFOLDS for r1 in R1_GROUPS for r2 in R2_GROUPS
    ]
    picks = rng.choice(len(combos), size=min(n, len(combos)), replace=False)

    rows = []
    for i, pick in enumerate(sorted(picks)):
        series, r1, r2 = combos[pick]
        molecule = Molecule.from_smiles(_fill(SCAFFOLDS[series], r1, r2))
        pic50 = float(np.clip(rng.normal(6.0, 0.9), 3.5, 9.5))
        rows.append(
            {
                "id": f"CMP-{10000 + i}",
                "molecule_obj": molecule,
                "series": series,
                "smiles": molecule.to_smiles(),
                "pIC50": round(pic50, 2),
                "solubility": round(float(rng.lognormal(3.5, 1.2)), 1),  # µM
                "MolWt": round(molecule.molecular_weight, 1),
                "cLogP": round(molecule.log_p_rdkit, 2),
                "TPSA": round(molecule.tpsa_rdkit, 1),
                "status": "Active" if pic50 >= 6.5 else "Inactive",
                "tested": (
                    datetime.date(2026, 1, 1)
                    + datetime.timedelta(days=int(rng.integers(0, 270)))
                ).isoformat(),
            }
        )
    return MoleculeDataFrame(
        polars.DataFrame(rows, schema_overrides={"molecule_obj": polars.Object}),
        init_substructure_lib=True,
    )
