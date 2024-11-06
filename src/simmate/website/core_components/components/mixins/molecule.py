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

    # Molecule searching

    # molecule = None  # moleclue_query
    # molecule_query_textinput = None
    # molecule_query_type = "similarity_2d"
    # # options: substructure, similarity, molecule_exact, similarity_2d

    # def unset_molecule(self):
    #     self.molecule = None
    #     self.call(
    #         "add_mol_sketcher",
    #         "molecule_query",
    #     )

    # def set_molecule(self, mol_str, render: bool = True):
    #     try:
    #         # text input takes priority
    #         if self.molecule_query_textinput:
    #             mol_str = self.molecule_query_textinput

    #         # This is an example mol_str given when *NOTHING* is in the chemdraw image
    #         # '"ACS Document 1996\r\n  ChemDraw09172414502D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
    #         # It will cause the from_dynamic to fail
    #         if mol_str.startswith(
    #             '"ACS Document 1996\r\n  ChemDraw'
    #         ) and mol_str.endswith(
    #             '2D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
    #         ):
    #             return  # there is no molecule to load

    #         molecule_obj = Molecule.from_dynamic(mol_str.strip('"'))
    #         self.molecule = molecule_obj.to_smiles()
    #         if render:
    #             self.call(
    #                 "add_mol_viewer",
    #                 "molecule_query",
    #                 molecule_obj.to_sdf(),
    #                 300,
    #                 300,
    #             )
    #     except:
    #         self.molecule = False

    # -------------------------------------------------------------------------
