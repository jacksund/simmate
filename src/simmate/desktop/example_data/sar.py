"""A synthetic SAR dataset: an R1 x R2 amide series with made-up (but plausible) activities."""

import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

CORE = Chem.MolFromSmarts("O=C(N)c1ccccc1")

# substituent SMILES -> made-up contribution to pIC50
R1_GROUPS = {
    "H": ("", 0.0),
    "F": ("F", 0.3),
    "Cl": ("Cl", 0.6),
    "Br": ("Br", 0.5),
    "Me": ("C", 0.2),
    "OMe": ("OC", 0.4),
    "CF3": ("C(F)(F)F", 0.9),
    "CN": ("C#N", 0.7),
    "OH": ("O", -0.3),
    "NH2": ("N", -0.5),
    "NO2": ("[N+](=O)[O-]", 0.1),
}
R2_GROUPS = {
    "methyl": ("C", 0.0),
    "ethyl": ("CC", 0.2),
    "isopropyl": ("C(C)C", 0.5),
    "cyclopropyl": ("C1CC1", 0.8),
    "phenyl": ("c1ccccc1", 1.1),
    "benzyl": ("Cc1ccccc1", 1.4),
    "hydroxyethyl": ("CCO", -0.2),
    "dimethylaminoethyl": ("CCN(C)C", 0.3),
    "oxan-4-yl": ("C1CCOCC1", 0.6),
}

PROPERTIES = ["pIC50", "cLogP", "MolWt", "TPSA", "HBD", "HBA", "RotBonds"]


def build_dataset(seed=7) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for r1_name, (r1, r1_effect) in R1_GROUPS.items():
        for r2_name, (r2, r2_effect) in R2_GROUPS.items():
            r1_part = f"({r1})" if r1 else ""
            mol = Chem.MolFromSmiles(f"O=C(N{r2})c1ccc{r1_part}cc1")
            logp = Crippen.MolLogP(mol)
            # Potency rises with the R-group effects but greasy compounds get penalized.
            pic50 = (
                5.5
                + r1_effect
                + r2_effect
                - 0.6 * max(0.0, logp - 3.5)
                + rng.normal(0, 0.2)
            )
            rows.append(
                {
                    "id": f"CPD-{len(rows) + 1:03d}",
                    "label": f"R1 = {r1_name}, R2 = {r2_name}",
                    "smiles": Chem.MolToSmiles(mol),
                    "mol": mol,
                    "pIC50": round(pic50, 2),
                    "cLogP": round(logp, 2),
                    "MolWt": round(Descriptors.MolWt(mol), 1),
                    "TPSA": round(rdMolDescriptors.CalcTPSA(mol), 1),
                    "HBD": Lipinski.NumHDonors(mol),
                    "HBA": Lipinski.NumHAcceptors(mol),
                    "RotBonds": Lipinski.NumRotatableBonds(mol),
                }
            )
    return rows
