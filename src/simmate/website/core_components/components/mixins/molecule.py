# -*- coding: utf-8 -*-

from django_unicorn.components import UnicornView

from simmate.toolkit import Molecule


class MoleculeInput(UnicornView):

    class Meta:
        javascript_exclude = ("user_options",)

    # -------------------------------------------------------------------------

    # Requires extra config such as:

    # requested_by_id = None

    # def mount(self):
    #     # set default starting values
    #     self.requested_by_id = self.request.user.id

    # -------------------------------------------------------------------------

    molecule = None  # stored as str (smiles or sdf)

    def set_molecule(self, mol_str):
        try:
            self.molecule = mol_str.strip('"')
            molecule_obj = Molecule.from_dynamic(self.molecule)
            self.call(
                "add_mol_viewer",
                "molecule_input",  # TODO: need to set this
                molecule_obj.to_sdf(),
                300,
                300,
            )
        except:
            self.molecule = False

        # check other datasets (see section below)
        if self.molecule:
            self.check_datasets()

    # -------------------------------------------------------------------------

    # Checking other datasets.

    molecule_match_urls: dict = {}
    datasets_to_check: list = ["__self_table__"]

    def check_datasets(self):

        # catch condition where no checks are needed
        if not self.datasets_to_check:
            return

        # BUG: state of molecule obj is not saved so we recreate
        # the object here. Ideally we could cache this...
        molecule_obj = Molecule.from_dynamic(self.molecule)

        if not molecule_obj:
            return  # not ready for queries (consider raising error)

        inchi_key = molecule_obj.to_inchi_key()
        for dataset_name in self.datasets_to_check:
            table, property_name = self.table_mappings[dataset_name]
            matches = [
                match.url for match in table.objects.filter(inchi_key=inchi_key).all()
            ]
            setattr(self, property_name, matches)

    # -------------------------------------------------------------------------
