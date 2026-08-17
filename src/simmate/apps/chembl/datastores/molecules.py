# -*- coding: utf-8 -*-

from simmate.toolkit.datastores import MoleculeDatastore


class ChemblMoleculeStore(MoleculeDatastore):
    """
    A MoleculeStore for the ChEMBL database, providing optimized search
    and retrieval of bioactive molecules.

    Steps to build:
        ``` python
        from simmate.apps.chembl.datastores import ChemblMoleculeStore
        # -----------------------------------
        ChemblMoleculeStore.convert_source_to_parquet()
        ChemblMoleculeStore.promote_staging()
        ```
    """

    app_name = "chembl"
    datastore_name = "molecules"

    @classmethod
    def convert_source_to_parquet(cls):
        """
        Converts molecule data directly from the ChEMBL database table into a
        single parquet file in the staging directory.
        """

        from simmate.database import connect  # isort: skip

        from ..models import ChemblMolecule

        exclude_columns = [
            "created_at",
            "updated_at",
            "molecule",
            "molecule_original",
            "inchi",
            "rdkit_mol",
            "fingerprint_morganbv",
            "functional_groups",
        ]
        columns = [
            c for c in ChemblMolecule.get_column_names() if c not in exclude_columns
        ]

        df = ChemblMolecule.objects.all().to_dataframe(
            columns=columns,
            engine="polars",
        )

        output_path = cls.staging_directory / "source.parquet"
        df.write_parquet(output_path)
