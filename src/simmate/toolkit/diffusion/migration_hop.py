# -*- coding: utf-8 -*-

import logging

from pymatgen.analysis.diffusion.neb.pathfinder import (
    MigrationHop as PymatgenMigrationHop,
)


class MigrationHop(PymatgenMigrationHop):
    def as_dict(self):
        # Pymatgen.diffusion has a broken as_dict method, so I need to fix this
        # here. I don't want to raise an error because I don't want issues
        # with the higher-level serialize_parameters utility
        return (
            "MigrationHop is not MSONable, and this bug is within pymatgen diffusion."
            "See https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/pull/264"
        )

    @classmethod
    def from_dynamic(cls, migration_hop):
        """
        This is an experimental feature. The code here is a repurposing of
        Structre.from_dynamic so consider making a general class for
        from_dynamic methods.
        """
        is_from_past_calc = False

        if isinstance(migration_hop, PymatgenMigrationHop):
            migration_hop_cleaned = migration_hop
        elif isinstance(migration_hop, dict) and "@module" in migration_hop.keys():
            migration_hop_cleaned = cls.from_dict(migration_hop)
        elif (
            isinstance(migration_hop, dict)
            and "migration_hop_table" in migration_hop.keys()
        ):
            is_from_past_calc = True
            migration_hop_cleaned = cls.from_database_dict(migration_hop)
        else:
            raise Exception("Unknown format provided for migration_hop input.")
        migration_hop_cleaned.is_from_past_calc = is_from_past_calc

        return migration_hop_cleaned

    @classmethod
    def from_database_dict(cls, migration_hop: dict):
        """
        This is an experimental feature. The code here is a repurposing of
        Structre.from_dynamic so consider making a general class for
        from_dynamic methods.

        ex:
            {
                "migration_hop_table": "MITMigrationHop",
                "migration_hop_id": 1,
            }
        """

        # Imports are done locally to keep this class modular.
        from django.utils.module_loading import import_string

        from simmate.database import connect
        from simmate.website.workflows import models as all_datatables

        datatable_str = migration_hop["migration_hop_table"]

        if hasattr(all_datatables, datatable_str):
            datatable = getattr(all_datatables, datatable_str)
        else:
            datatable = import_string(datatable_str)
        # for now I only support migration_hop_id
        migration_hop_db = datatable.objects.get(id=migration_hop["migration_hop_id"])
        migration_hop_cleaned = migration_hop_db.to_toolkit()
        migration_hop_cleaned.database_entry = migration_hop_db

        return migration_hop_cleaned

    def get_sc_structures(
        self,
        vac_mode: bool = True,
        min_atoms: int = 80,
        max_atoms: int = 240,
        min_length: float = 10.0,
        tol: float = 1e-5,
    ):

        supercell_start, supercell_end, supercell_base = super().get_sc_structures(
            vac_mode, min_atoms, max_atoms, min_length, tol
        )

        # The parent method doesn't work as itended... I don't want to fix it,
        # so I just warn users.
        if supercell_start.num_sites < min_atoms or supercell_end.num_sites > max_atoms:
            logging.warning(
                f"Failed to meet min_atoms={min_atoms} and max_atoms={max_atoms} "
                "requirements when making supercell. Resulted in"
                f" {supercell_start.num_sites} atoms."
            )
        if min(supercell_start.lattice.lengths) < min_length:
            logging.warning(
                "Failed to meet min_length={min_length} requirement when"
                " making supercell. Resulted in lattice vectors lengths of "
                f"{supercell_start.lattice.lengths}."
            )

        # BUG-CHECK: There's some rounding issue in the base code that I don't want
        # to mess with, so I just hack fix here.
        try:
            assert supercell_start != supercell_end
        except:
            raise Exception(
                "This structure has a bug due to a rounding error. "
                "Our team is aware of this bug and it has been fixed for the next "
                "pymatgen-analysis-diffusion release. In the meantime, we've found "
                "that increasing your supercell tolerances (min_atoms, max_atoms, min_length)"
                "can sometimes fix this error."
            )
        ####

        return supercell_start, supercell_end, supercell_base
