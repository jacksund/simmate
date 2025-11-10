# -*- coding: utf-8 -*-

import logging

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule


class MoleculeInput:

    search_inputs = [
        "molecule",
        # "molecule_query_type",
    ]

    # -------------------------------------------------------------------------

    # TODO
    # For input_type == "reference":
    # is_molecule_ref = False
    # molecule_ref_table = None

    def load_molecule(self, input_name: str):

        # There are 4 options for mol inputs: custom, ref (e.g. an ID), text, and sketcher
        # The order of priority is... custom -> ref -> text -> sketcher.
        # Here we go through and find the first that is present in the form_data
        input_types = [
            "custom",
            "reference",
            # TODO: add file upload option
            "text",
            "sketcher",
        ]
        found_type = False
        for input_type in input_types:
            molecule_input = self.form_data.pop(
                f"{input_name}__molecule_{input_type}", None
            )
            if molecule_input:
                found_type = True
                break
        if not found_type:
            logging.warning(f"Failed to find non-null input: '{input_name}'")
            return  # nothing to load

        # This is an example mol_str given when *NOTHING* is in the chemdraw image
        # '"ACS Document 1996\r\n  ChemDraw09172414502D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
        # It will cause the from_dynamic to fail.
        # The JS checks for this, but it doesn't hurt to check for this again here.
        if molecule_input is None or (
            len(input_type) < 100
            and input_type.startswith('"ACS Document 1996\r\n  ChemDraw')
            and input_type.endswith(
                '2D\r\n\r\n  0  0  0  0  0  0  0  0  0  0999 V2000\r\nM  END\r\n"'
            )
        ):
            return  # nothing to load

        if input_type in ["sketcher", "text"]:
            try:
                molecule_obj = Molecule.from_dynamic(molecule_input)
                self.form_data[f"{input_name}__molecule_original"] = molecule_input
                self.form_data[input_name] = molecule_obj
            except:
                logging.warning(
                    f"Failed to load molecule for input '{input_name}': '{molecule_input}'"
                )
                self.form_data[input_name] = False  # to display error
                molecule_obj = None

        elif input_type == "reference":
            # The most common custom input is an entry ID that points to some other
            # molecule table.
            assert self.is_molecule_ref and self.molecule_ref_table

            try:
                db_mol = self.molecule_ref_table.objects.get(
                    id=self.molecule_custom_input
                )
                self.molecule_ref_id = db_mol.id  # should equal the custom input val
                self.molecule = db_mol.molecule  # sdf string
                self._molecule_obj = db_mol.to_toolkit()
            except:
                self.molecule = False

        elif input_type == "custom":
            self.load_molecule_custom(input_name)

        # if this is a relation field, we need to ensure the pointer id is set
        # if self.molecule and self.is_molecule_ref and not self.molecule_ref_id:
        #     try:
        #         # BUG: what if there is more than one match below?
        #         db_mol = self.molecule_ref_table.objects.get(
        #             inchi_key=self._molecule_obj.to_inchi_key()
        #         )
        #         self.molecule_ref_id = db_mol.id
        #     except:
        #         self.molecule = False

        # NOTE: if the load methods above failed, then we exit early
        if not molecule_obj:
            return

        if self.form_mode == "create" and self.molecule_match_tables:
            matches = self.check_datasets(molecule_obj)
            self.form_data[f"{input_name}__molecule_matches"] = matches
            if matches:
                self.skip_db_save = True
            # TODO: are there cases where we allow duplicates? eg
            # allow_molecule_matches: bool = False
            # if self.molecule_matches and not self.allow_molecule_matches:
            #     self.errors.append(
            #         f"This molecule has already been added to {table.table_name}"
            #     )

        # draw mol image
        self.js_actions = [
            {
                "add_mol_viewer": [
                    f"{input_name}-{self.component_id}-image",
                    molecule_obj.to_sdf(),
                    300,
                    300,
                ]
            }
        ]

    def load_molecule_custom(self, input_name: str):
        raise NotImplementedError("No custom `load_molecule_custom` method is defined")

    # -------------------------------------------------------------------------

    # Checking other datasets for exact match

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

    # -------------------------------------------------------------------------

    # def load_many_molecules(self, mol_str: str):
    #     try:
    #         molecules = Molecule.from_dynamic(mol_str).components
    #         self.molecule = True  # indicates successful load in templates

    #         self.entries_for_create_many = []
    #         for molecule in molecules:
    #             entry = {}
    #             entry["molecule"] = molecule.to_sdf()
    #             if self.form_mode == "create_many" and self.molecule_match_tables:
    #                 entry["molecule_matches"] = self.check_datasets(molecule)
    #                 entry["skip_db_save"] = True if entry["molecule_matches"] else False
    #             self.entries_for_create_many.append(entry)

    #         # draw molecules in ui
    #         for i, entry in enumerate(self.entries_for_create_many):
    #             self.call(
    #                 "add_mol_viewer",
    #                 f"{i}_{self.component_name}_molecule",
    #                 entry["molecule"],  # sdf str
    #                 100,
    #                 100,
    #             )
    #         # in case the form automatically creates new dropdowns. Though
    #         # this typically isn't needed.
    #         self.call("refresh_select2")
    #     except:
    #         self.molecule = False

    # def unset_molecule(self):
    #     name = "molecule"  # TODO: accept as kwarg
    #     self.molecule = None
    #     self.molecule_text_input = None
    #     self.call(
    #         "add_mol_sketcher",
    #         # {{ name }}{{ context.unicorn.component_key }}
    #         f"{name}{self.component_key}",
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

    def set_similarity_3d(self, value):
        self.molecule_query_type = "similarity_3d"
        self.molecule_text_input = value
        # self.set_molecule(value)

    # -------------------------------------------------------------------------
