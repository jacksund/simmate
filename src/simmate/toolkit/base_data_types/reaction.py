# -*- coding: utf-8 -*-

from pathlib import Path

from rdkit.Chem import AllChem, Draw

from .molecule import Molecule


class Reaction:

    def __init__(
        self,
        reactants: list[Molecule],
        products: list[Molecule],
        reagents: list[Molecule] = [],
        reagent_amounts: list[dict] = [],  # list equivs or exact amounts
        dynamic_load: bool = True,  # if you already have Mol objs, set this to false for speedup
    ):

        if not reactants:
            raise Exception("At least one reactant is required for a Reaction")

        if not products:
            raise Exception("At least one product is required for a Reaction")

        if dynamic_load:
            reactants = [Molecule.from_dynamic(m) for m in reactants]
            products = [Molecule.from_dynamic(m) for m in products]
            reagents = [Molecule.from_dynamic(m) for m in reagents]

        self.reactants = reactants
        self.reagents = reagents
        self.products = products
        self.reagent_amounts = reagent_amounts

    @property
    def image(self):
        """
        Prints an image of the reaction if using an iPython-based console
        (e.g. iPython, Spyder IDE, Jupyter Notebook, etc.)
        """
        return self.rdkit_reaction

    @property
    def rdkit_reaction(self):
        return AllChem.ReactionFromSmarts(
            self.to_smiles(),
            useSmiles=not self.is_reaction_template,
        )

    # -------------------------------------------------------------------------

    # INPUT METHODs (STRING-TYPES)

    @classmethod
    def from_smiles(cls, smiles: str, **kwargs):
        if ">" not in smiles:
            raise Exception("Only reaction-based SMILES/SMARTS are accepted.")

        # note this will split via 'reactants>reagents>>products'
        reactants, reagents, products = [s.split(".") for s in smiles.split(">")]
        return cls(
            reactants=reactants,
            reagents=reagents,
            products=products,
            **kwargs,
        )

    @classmethod
    def from_smarts(cls, smarts: str, **kwargs):
        return cls.from_smiles(smarts, **kwargs)  # just an alias for now

    # -------------------------------------------------------------------------

    # OUTPUT METHODs (STRING-TYPES)

    def to_smiles(self):
        reactants_smiles = [m.to_smiles() for m in self.reactants]
        reagents_smiles = [m.to_smiles() for m in self.reagents]
        products_smiles = [m.to_smiles() for m in self.products]
        final_smiles = (
            ".".join(reactants_smiles)
            + ">"
            + ".".join(reagents_smiles)
            + ">"
            + ".".join(products_smiles)
        )
        return final_smiles

    def to_png(self, height: int = 800, width: int = 300, highlight: bool = True):
        """
        Generates a PIL image object. Use `to_png_file` if you instead want to
        write the image directly to a file.
        """
        d2d = Draw.MolDraw2DCairo(height, width)
        d2d.DrawReaction(self.rdkit_reaction, highlightByReactant=highlight)
        png = d2d.GetDrawingText()
        return png

    # -------------------------------------------------------------------------

    # OUTPUT METHODS (FILE-TYPES)

    def to_png_file(self, filename: str | Path):
        """
        Outputs the `Molecule` object to a PNG image file. The image is drawn
        using RDkit
        """
        with open(filename, "wb+") as file:
            file.write(self.to_png())

    # -------------------------------------------------------------------------

    # TEMPLATE HELPER METHODS
    # template = R groups are in the reaction and we want to run with a specific
    # R value OR with a molecule to replace the molecule with the R component

    @property
    def template_reactants(self):
        return [m for m in self.reactants if m.is_smarts]

    @property
    def template_products(self):
        return [m for m in self.products if m.is_smarts]

    @property
    def is_reaction_template(self):
        return True if self.template_reactants or self.template_products else False

    @property
    def template_rdkit_reaction(self):

        # similar with to_smiles, except we only include SMARTS-based react/prods
        reactants_smiles = [m.to_smiles() for m in self.template_reactants]
        products_smiles = [m.to_smiles() for m in self.template_products]
        final_smiles = ".".join(reactants_smiles) + ">>" + ".".join(products_smiles)
        return AllChem.ReactionFromSmarts(final_smiles)

    def apply_template(self, reactants: list[Molecule]) -> list[Molecule]:
        # OPTIMIZE: this calls RunReactants one set at a time
        rdkit_rxn = self.template_rdkit_reaction
        rdkit_reactants = tuple([r.rdkit_molecule for r in reactants])
        rdkit_products = rdkit_rxn.RunReactants(tuple(rdkit_reactants))[0]

        # BUG: rdkit doesn't fully initialize the mol objs... causing downstream
        # methods like mol.get_morgan_fingerprint() to fail. To fix this,
        # we convert to smiles and then immediately reload it using from_smiles.
        # Without this bug, here's what the more basic line would be:
        #   return [Molecule.from_rdkit(p) for p in rdkit_products]
        return [
            Molecule.from_smiles(Molecule.from_rdkit(p).to_smiles())
            for p in rdkit_products
        ]

    # -------------------------------------------------------------------------
