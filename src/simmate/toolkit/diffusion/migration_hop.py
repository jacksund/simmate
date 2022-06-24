# -*- coding: utf-8 -*-

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
        from simmate.database import connect
        from simmate.website.workflows import models as all_datatables
        from django.utils.module_loading import import_string

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
