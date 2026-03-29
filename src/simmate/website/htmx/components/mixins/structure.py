# -*- coding: utf-8 -*-

import logging

from simmate.database.core import DatabaseTable
from simmate.toolkit import Structure


class StructureInput:

    def load_structure(self, input_name: str = "structure"):
        """
        Handles loading a structure from various input types: file, database, or URL.
        """
        # The priority of input types is: file -> url -> database
        input_types = [
            "file",
            "url",
            "database_id",
        ]

        found_type = False
        for t in input_types:
            # We use f"{input_name}__{t}" for consistency with MoleculeInput
            i = self.form_data.pop(f"{input_name}__{t}", None)
            if i and not found_type and i not in ["None"]:
                found_type = True
                input_type = t
                structure_input = i
                # we continue to loop to pop() all other keys

        if not found_type:
            logging.warning(f"Failed to find non-null input: '{input_name}'")
            return

        try:
            if input_type == "file":
                if not isinstance(structure_input, Structure):
                    # This should already be a Structure object if handled by parse_file_item
                    structure_obj = Structure.from_dynamic(structure_input)
                else:
                    structure_obj = structure_input

            elif input_type == "url":
                url_decomp = [x for x in structure_input.split("/") if x]
                structure_obj = DatabaseTable.from_dict(
                    {
                        "database_table": url_decomp[-2],
                        "database_id": url_decomp[-1],
                    }
                ).to_toolkit()

            elif input_type == "database_id":
                table_name = self.form_data.pop(f"{input_name}__database_table", None)
                structure_obj = DatabaseTable.from_dict(
                    {
                        "database_table": table_name,
                        "database_id": structure_input,
                    }
                ).to_toolkit()

            self.form_data[input_name] = structure_obj

            # trigger JS to render the structure
            self.js_actions.append(
                {
                    "add_threejs_render": [
                        f"{input_name}-{self.component_id}-viewer",
                        structure_obj.to_threejs_json(),
                    ]
                }
            )

        except Exception as e:
            logging.warning(
                f"Failed to load structure for input '{input_name}' of type '{input_type}': {e}"
            )
            self.form_data[input_name] = False  # to display error
            return

    def unset_structure(self, input_name: str = "structure"):
        self.form_data.pop(input_name, None)
        # also pop any lingering input values
        for t in ["file", "url", "database_id", "database_table"]:
            self.form_data.pop(f"{input_name}__{t}", None)
