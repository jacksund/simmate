# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.toolkit import Structure
from simmate.website.data_explorer.components import DynamicTableForm
from simmate.website.htmx.components import (
    MoleculeInput,
    StructureInput,
)

from ..models import Substance


class SubstanceForm(DynamicTableForm, MoleculeInput, StructureInput):
    table = Substance

    display_name = "Chemical Substances"
    description_short = (
        "A substance is a specific element or compound with uniform composition+structure. "
        "As a general rule of thumb, if there is a CAS number (from ACS) or "
        "CID (from PubChem) assigned to it, then it is likely a chemical substance. "
        "In addition, this table includes both specified and unspecified "
        "stereochemical compounds, where flat structures and those with "
        "'and'/'or' notations are separate entries. Allotropes are also "
        "separate entries."
    )

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "inventory_management/substance/table.html",
        "entry": "inventory_management/substance/view.html",
    }
    template_name = "inventory_management/substance/form.html"

    enabled_forms = [
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "id"

    # -------------------------------------------------------------------------

    def mount_for_update(self):
        super().mount_for_update()

        # handle molecule viewer
        molecule_db = self.form_data.get("molecule")
        if molecule_db:
            # check if it's already a toolkit obj or needs conversion
            molecule_toolkit = (
                molecule_db
                if isinstance(molecule_db, ToolkitMolecule)
                else molecule_db.to_toolkit()
            )
            self.js_actions.append(
                {
                    "add_mol_viewer": [
                        f"molecule-{self.component_id}-image",
                        molecule_toolkit.to_sdf(),
                        300,
                        300,
                    ]
                }
            )

        # handle structure viewer
        structure_db = self.form_data.get("structure")
        if structure_db:
            structure_toolkit = (
                structure_db
                if isinstance(structure_db, Structure)
                else structure_db.to_toolkit()
            )
            self.js_actions.append(
                {
                    "add_threejs_render": [
                        f"structure-{self.component_id}-viewer",
                        structure_toolkit.to_threejs_json(),
                    ]
                }
            )

    def unmount_for_create(self):
        super().unmount_for_create()
        self._handle_toolkit_objects()

    def unmount_for_update(self):
        super().unmount_for_update()
        self._handle_toolkit_objects()

    def _handle_toolkit_objects(self):
        # handle molecule
        molecule_toolkit = self.form_data.get("molecule")
        if molecule_toolkit and isinstance(molecule_toolkit, ToolkitMolecule):
            from ..models import Molecule

            inchi_key = molecule_toolkit.to_inchi_key()
            molecule_db, created = Molecule.objects.get_or_create(
                inchi_key=inchi_key,
                defaults=Molecule.from_toolkit(as_dict=True, molecule=molecule_toolkit),
            )
            self.table_entry.molecule = molecule_db

        # handle structure
        structure_toolkit = self.form_data.get("structure")
        if structure_toolkit and isinstance(structure_toolkit, Structure):
            from ..models import Structure as DBStructure

            # TODO: matching?
            structure_db = DBStructure.objects.create(
                **DBStructure.from_toolkit(as_dict=True, structure=structure_toolkit)
            )
            self.table_entry.structure = structure_db

    def on_change_hook__structure__file(self):
        self.load_structure("structure")

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        # most inputs for substance are optional, ID is generated automatically
        "substance_type",
    ]

    def check_form_for_create(self):
        super().check_form_for_create()
        # id is auto-generated in postsave_to_db or handled manually if not set
        if not self.form_data.get("id"):
            self.form_data["id"] = Substance.generate_id()

        # also set registered_by to current user
        if not self.form_data.get("registered_by_id"):
            self.form_data["registered_by_id"] = self.request.user.id

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "substance_type",
        "description",
        "is_theoretical",
        "is_delisted",
        "is_private",
        "is_unknown",
        "common_name",
        "iupac_name",
        "synonyms",
        "molecule",
        "structure",
        "is_primary",
        "parent",
        "is_metastable",
        "stereochem_type",
        "bcpc",
        "cas_number",
        "chembl",
        "chemspace",
        "emolecules",
        "enamine",
        "pdb",
        "ppdb",
        "pubchem_cid",
        "aflow",
        "cod",
        "jarvis",
        "materials_project",
        "oqmd",
        "extra_metadata",
    ]
