# -*- coding: utf-8 -*-

import numpy

from simmate.database.base_data_types import DatabaseTable, table_column


class Forces(DatabaseTable):

    """Base Info"""

    # A list of forces for each atomic site (eV/AA). So this is a list like...
    # [site1, site2, site3, ...] where site1=[force_x, force_y, force_z]
    site_forces = table_column.JSONField(blank=True, null=True)

    # This is 3x3 matrix that represents the stress on the structure lattice
    lattice_stress = table_column.JSONField(blank=True, null=True)

    """ Query-helper Info """

    # Reports the vector norm for the site with the highest forces on it
    site_force_norm_max = table_column.FloatField(blank=True, null=True)

    # Takes the site forces and reports the vector norm for it.
    # See numpy.linalg.norm for how this is calculated.
    site_forces_norm = table_column.FloatField(blank=True, null=True)
    site_forces_norm_per_atom = table_column.FloatField(blank=True, null=True)

    # Takes the site forces and reports the vector norm for it.
    # # See numpy.linalg.norm for how this is calculated.
    lattice_stress_norm = table_column.FloatField(blank=True, null=True)
    lattice_stress_norm_per_atom = table_column.FloatField(blank=True, null=True)

    """ Relationships """
    # The data should link directly to a specific structure
    # structure = table_column.ForeignKey(Structure, on_delete=table_column.PROTECT)
    # OR should this inherit from the Structure class too...?

    """ Model Methods """
    # TODO: add a from_ionic_step method in the future when I have this class.

    @classmethod
    def from_base_data(
        cls, structure, site_forces=None, lattice_stress=None, as_dict=False
    ):
        # Given site forces and lattice stress, this function builds the rest of
        # the required fields for this class as a dictionary.

        site_data = (
            dict(
                site_forces=site_forces,
                site_force_norm_max=max([numpy.linalg.norm(f) for f in site_forces]),
                site_forces_norm=numpy.linalg.norm(site_forces),
                site_forces_norm_per_atom=numpy.linalg.norm(site_forces)
                / structure.num_sites,
            )
            if site_forces
            else {}
        )

        lattice_data = dict(
            lattice_stress=lattice_stress,
            lattice_stress_norm=numpy.linalg.norm(lattice_stress),
            lattice_stress_norm_per_atom=numpy.linalg.norm(lattice_stress)
            / structure.num_sites,
        )

        all_data = dict(**site_data, **lattice_data)

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)

    """ Set as Abstract Model """
    # I have other models inherit from this one, while this model doesn't need
    # its own table.
    class Meta:
        abstract = True
