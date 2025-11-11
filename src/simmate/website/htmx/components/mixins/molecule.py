# -*- coding: utf-8 -*-

import logging

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule


class MoleculeInput:

    ignore_on_search = ["molecule_query_type"]

    # -------------------------------------------------------------------------

    molecule_query_type = "similarity_2d"  # sets default value
    molecule_query_type_options = [
        ("molecule_exact", "Exact match"),
        ("molecule_list_exact", "Exact match (list of molecules)"),
        ("substructure", "Substructure"),
        ("scaffold", "Scaffold (R-groups)"),
        ("similarity_2d", "Similarity (2D, basic)"),
        # ("similarity_3d", "Similarity (3D, FastROCS)"),
    ]

    # -------------------------------------------------------------------------

    # For when input_type="reference"
    molecule_ref_table = None

    # -------------------------------------------------------------------------

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

        # How the molecule is loaded varies depending on the input type and
        # form mode. We want to notify users when the load fails too, which
        # is why we put this whole section in a try/except
        try:

            if input_type in ["sketcher", "text"]:

                if self.form_mode == "search":
                    query_type = self.form_data["molecule_query_type"]
                    # TODO: better loading for SMARTS
                    # if query_type == "molecule_exact":
                    #     pass
                    # elif query_type == "molecule_list_exact":
                    #     pass
                    # elif query_type == "substructure":
                    #     pass
                    # elif query_type == "scaffold":
                    #     pass
                    # elif query_type == "similarity_2d":
                    #     pass
                    molecule_obj = Molecule.from_dynamic(molecule_input)
                    self.form_data[query_type] = molecule_obj.to_smiles()
                    # BUG: format means we can't search the related field
                    # f"{input_name}__{query_type}" would be better

                    # so that the image renders but we don't have any loose
                    # value sitting in the form
                    setattr(self, input_name, True)

                else:
                    molecule_obj = Molecule.from_dynamic(molecule_input)
                    self.form_data[f"{input_name}__molecule_original"] = molecule_input
                    self.form_data[input_name] = molecule_obj

            elif input_type == "reference":
                raise NotImplementedError()
                # db_mol = self.molecule_ref_table.objects.get(
                #     id=self.molecule_custom_input
                # )
                # self.molecule_ref_id = db_mol.id  # should equal the custom input val
                # self.molecule = db_mol.molecule  # sdf string
                # self._molecule_obj = db_mol.to_toolkit()

            elif input_type == "custom":
                self.load_molecule_custom(input_name)

        except:
            logging.warning(
                f"Failed to load molecule for input '{input_name}' of type '{input_type}': '{molecule_input}'"
            )
            self.form_data[input_name] = False  # to display error
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
