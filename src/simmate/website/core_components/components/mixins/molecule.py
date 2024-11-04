# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule


class MoleculeInput:

    class Meta:
        javascript_exclude = ("molecule_match_tables",)

    # -------------------------------------------------------------------------

    molecule = None  # stored as str (smiles or sdf)

    def get_molecule_obj(self):
        # OPTIMIZE: consider caching this
        return Molecule.from_dynamic(self.molecule)

    def set_molecule(self, mol_str: str):
        try:
            self.molecule = mol_str.strip('"')
            molecule_obj = self.get_molecule_obj()
            self.call(
                "add_mol_viewer",
                "molecule",  # TODO: need to set this
                molecule_obj.to_sdf(),
                300,
                300,
            )
        except:
            self.molecule = False

        # check other datasets (see section below)
        if self.molecule and self.molecule_match_tables:
            self.check_datasets()

    # -------------------------------------------------------------------------

    # Checking other datasets.

    molecule_matches: list[dict] = []
    molecule_match_tables: list = []  # ["__self__"]

    def check_datasets(self):

        molecule_obj = self.get_molecule_obj()
        inchi_key = molecule_obj.to_inchi_key()

        all_matches = []
        for table_name in self.molecule_match_tables:

            if table_name == "__self__":
                table = self.table
            else:
                table = DatabaseTable.get_table(table_name)

            matches = [
                match.url for match in table.objects.filter(inchi_key=inchi_key).all()
            ]
            if matches:
                all_matches.append(
                    {
                        "table_name": table.table_name,
                        "urls": matches,
                    }
                )

        self.molecule_matches = all_matches

    # TODO:
    # allow_molecule_matches: bool = False
    # if self.molecule_matches and not self.allow_molecule_matches:
    #     self.errors.append(
    #         f"This molecule has already been added to {table.table_name}"
    #     )

    # -------------------------------------------------------------------------
