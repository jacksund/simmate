# -*- coding: utf-8 -*-

import numpy

from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.toolkit import Structure as ToolkitStructure


class Forces(DatabaseTable):
    class Meta:
        abstract = True

    exclude_from_summary = [
        "site_forces",
        "lattice_stress",
    ]

    archive_fields = [
        "site_forces",
        "lattice_stress",
    ]

    api_filters = dict(
        site_force_norm_max=["range"],
        site_forces_norm_per_atom=["range"],
        lattice_stress_norm=["range"],
        lattice_stress_norm_per_atom=["range"],
    )

    site_forces = table_column.JSONField(blank=True, null=True)
    """
    A list of forces for each atomic site (eV/AA). So this is a list like...
    ```
    [site1, site2, site3, ...] 
    ```
    ... where ...
    ```
    site1=[force_x, force_y, force_z]
    ```
    """

    lattice_stress = table_column.JSONField(blank=True, null=True)
    """
    The is 3x3 matrix that represents stress on the structure lattice
    """

    site_force_norm_max = table_column.FloatField(blank=True, null=True)
    """
    Reports the vector norm for the site with the highest forces on it
    """

    site_forces_norm = table_column.FloatField(blank=True, null=True)
    """
    Takes the site forces and reports the vector norm for it.

    See numpy.linalg.norm for how this is calculated.
    """

    site_forces_norm_per_atom = table_column.FloatField(blank=True, null=True)
    """
    site_forces_norm divided by nsites
    """

    lattice_stress_norm = table_column.FloatField(blank=True, null=True)
    """
    Takes the site forces and reports the vector norm for it.

    See numpy.linalg.norm for how this is calculated.
    """

    lattice_stress_norm_per_atom = table_column.FloatField(blank=True, null=True)
    """
    lattice_stress_norm divided by nsites
    """

    @classmethod
    def _from_toolkit(
        cls,
        structure: ToolkitStructure | str = None,
        site_forces=None,
        lattice_stress=None,
        as_dict=False,
    ):
        """
        Given site forces and lattice stress, this function builds the rest of
        the required fields for this class as a dictionary.
        """

        if isinstance(structure, str):
            structure = ToolkitStructure.from_database_string(structure)

        # TODO: in the future, this should accept an IonicStep toolkit object
        # or maybe Structure + Forces toolkit objects.
        site_data = (
            dict(
                site_forces=site_forces,
                site_force_norm_max=float(
                    max([numpy.linalg.norm(f) for f in site_forces])
                ),
                site_forces_norm=float(numpy.linalg.norm(site_forces)),
                site_forces_norm_per_atom=float(
                    numpy.linalg.norm(site_forces) / structure.num_sites
                )
                if structure
                else None,
            )
            if site_forces
            else {}
        )

        lattice_data = (
            dict(
                lattice_stress=lattice_stress,
                lattice_stress_norm=float(numpy.linalg.norm(lattice_stress)),
                lattice_stress_norm_per_atom=float(
                    numpy.linalg.norm(lattice_stress) / structure.num_sites
                )
                if structure
                else None,
            )
            if lattice_stress
            else {}
        )

        all_data = dict(**site_data, **lattice_data)

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)
