# -*- coding: utf-8 -*-

"""
This module is experimental and subject to change.
"""

from pymatgen.electronic_structure.dos import CompleteDos

from simmate.database.base_data_types import table_column, DatabaseTable


class DensityofStates(DatabaseTable):
    class Meta:
        abstract = True

    # uses vasprun.complete_dos.as_dict()
    density_of_states_data = table_column.JSONField(blank=True, null=True)
    # !!! Consider breaking down data into...
    #   total
    #   elemental -- dict of ["total", "s", "p", "d", "f"], ["1", "-1"]
    #   orbital

    band_gap = table_column.FloatField(blank=True, null=True)
    energy_fermi = table_column.FloatField(blank=True, null=True)
    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    valence_band_maximum = table_column.FloatField(blank=True, null=True)
    # spin_polarization (float "Spin polarization at the fermi level.")
    # magnetic_ordering (Magnetic ordering of the calculation.)

    @classmethod
    def _from_toolkit(
        cls,
        density_of_states: CompleteDos = None,
        as_dict=False,
    ):
        # Given energy, this function builds the rest of the required fields
        # for this class as an object (or as a dictionary).
        data = (
            dict(
                density_of_states_data=density_of_states.as_dict(),
                band_gap=density_of_states.get_gap(),
                energy_fermi=density_of_states.efermi,
                conduction_band_minimum=density_of_states.get_cbm_vbm()[0],
                valence_band_maximum=density_of_states.get_cbm_vbm()[1],
            )
            if density_of_states
            else {}
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return data if as_dict else cls(**data)
