# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule


class MoleculeInput:

    class Meta:
        javascript_exclude = (
            "molecule_match_tables",
            "molecule_query_type_options",
        )

    search_inputs = [
        "molecule",
        # "molecule_query_type",
    ]

    # -------------------------------------------------------------------------

    molecule = None  # stored as str (smiles or sdf)
    _molecule_obj = None

    # molecule_sketcher_input --> pass to methods directly (the "mol_str" kwarg)
    molecule_text_input = None
    molecule_custom_input = None

    def set_molecule(self, mol_str: str):

        # TODO:
        # text input takes priority
        # if self.molecule_text_input:
        #     mol_str = self.molecule_text_input
        # # This is an example mol_str given when *NOTHING* is in the chemdraw image
        # # '"ACS Document 1996\r\n  ChemDraw09172414502D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
        # # It will cause the from_dynamic to fail
        # if mol_str.startswith(
        #     '"ACS Document 1996\r\n  ChemDraw'
        # ) and mol_str.endswith(
        #     '2D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
        # ):
        #     return  # there is no molecule to load

        try:

            self.molecule = mol_str.strip('"')
            self._molecule_obj = Molecule.from_dynamic(self.molecule)

            if self.form_mode == "create" and self.molecule_match_tables:
                self.molecule_matches = self.check_datasets(self._molecule_obj)
            if self.molecule_matches:
                self.skip_db_save = True

            self.call(
                "add_mol_viewer",
                "molecule",  # TODO: need to set this
                self._molecule_obj.to_sdf(),
                300,
                300,
            )

        except:
            self.molecule = False

    def load_many_molecules(self, mol_str: str):
        try:
            molecules = Molecule.from_dynamic(mol_str).components
            self.molecule = True  # indicates successful load in templates

            self.entries_for_create_many = []
            for molecule in molecules:
                entry = {}
                entry["molecule"] = molecule.to_sdf()
                if self.form_mode == "create_many" and self.molecule_match_tables:
                    entry["molecule_matches"] = self.check_datasets(molecule)
                    entry["skip_db_save"] = True if entry["molecule_matches"] else False
                self.entries_for_create_many.append(entry)

            # draw molecules in ui
            for i, entry in enumerate(self.entries_for_create_many):
                self.call(
                    "add_mol_viewer",
                    f"{i}_{self.component_name}_molecule",
                    entry["molecule"],  # sdf str
                    100,
                    100,
                )
            # in case the form automatically creates new dropdowns. Though
            # this typically isn't needed.
            self.call("refresh_select2")
        except:
            self.molecule = False

    def unset_molecule(self):
        name = "molecule"  # TODO: accept as kwarg

        self.molecule = None
        self.molecule_text_input = None
        self.call(
            "add_mol_sketcher",
            # {{ name }}{{ context.unicorn.component_key }}
            f"{name}{self.component_key}",
        )

    # -------------------------------------------------------------------------

    # Checking other datasets.

    molecule_matches: list[dict] = []
    molecule_match_tables: list = []  # ["__self__"] is most common

    def check_datasets(self, molecule: Molecule) -> list[dict]:

        inchi_key = molecule.to_inchi_key()

        all_matches = []
        for table_name in self.molecule_match_tables:

            if table_name == "__self__":
                table = self.table
            else:
                table = DatabaseTable.get_table(table_name)

            for db_obj in table.objects.filter(inchi_key=inchi_key).all():
                all_matches.append(
                    {
                        "table_name": db_obj.table_name,
                        "table_entry_id": db_obj.id,
                        "table_entry_url": db_obj.url,
                    }
                )

        return all_matches

    # TODO:
    # allow_molecule_matches: bool = False
    # if self.molecule_matches and not self.allow_molecule_matches:
    #     self.errors.append(
    #         f"This molecule has already been added to {table.table_name}"
    #     )

    # -------------------------------------------------------------------------

    # Molecule searching

    molecule_query_type = "similarity_2d"
    molecule_query_type_options = [
        ("molecule_exact", "Exact match"),
        ("molecule_list_exact", "Exact match (list of molecules)"),
        ("substructure", "Substructure"),
        ("similarity_2d", "Similarity (2D, basic)"),
        # ("similarity_3d", "Similarity (3D, FastROCS)"),
    ]

    # methods to help with mounting GET kwargs

    def set_molecule_exact(self, value):
        self.molecule_query_type = "molecule_exact"
        self.molecule_text_input = value
        # self.set_molecule(value)

    def set_molecule_list_exact(self, value):
        self.molecule_query_type = "molecule_list_exact"
        self.molecule_text_input = value
        # self.set_molecule(value)

    def set_substructure(self, value):
        self.molecule_query_type = "substructure"
        self.molecule_text_input = value
        # self.set_molecule(value)

    def set_similarity_2d(self, value):
        self.molecule_query_type = "similarity_2d"
        self.molecule_text_input = value
        # self.set_molecule(value)

    # def set_similarity_3d(self, value):
    #     self.molecule_query_type = "similarity_3d"
    #     self.molecule_text_input = value
    #     # self.set_molecule(value)

    # -------------------------------------------------------------------------
