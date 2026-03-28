# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Substance


class SubstanceForm(DynamicTableForm):
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
