# -*- coding: utf-8 -*-

"""
This module is experimental and subject to change.
"""


from pymatgen.electronic_structure.bandstructure import (
    BandStructure as ToolkitBandStructure,
)

from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Calculation,
    Structure,
)


class BandStructure(DatabaseTable):
    class Meta:
        abstract = True

    base_info = ["band_structure_data"]

    # kpt_path_type (setyawan_curtarolo, hinuma, latimer_munro)
    # Maybe set as an abstract property?

    band_structure_data = table_column.JSONField(blank=True, null=True)
    # uses vasprun.get_band_structure(line_mode=True).as_dict()

    nbands = table_column.IntegerField(blank=True, null=True)
    band_gap = table_column.FloatField(blank=True, null=True)
    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    band_gap_direct = table_column.FloatField(blank=True, null=True)
    energy_fermi = table_column.FloatField(blank=True, null=True)
    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    valence_band_maximum = table_column.FloatField(blank=True, null=True)
    is_metal = is_gap_direct = table_column.BooleanField(blank=True, null=True)
    # magnetic_ordering (Magnetic ordering of the calculation.)
    # equivalent_labels (Equivalent k-point labels in other k-path conventions)

    @classmethod
    def _from_toolkit(
        cls,
        band_structure: ToolkitBandStructure = None,
        as_dict=False,
    ):
        # Given energy, this function builds the rest of the required fields
        # for this class as an object (or as a dictionary).
        data = (
            dict(
                band_structure_data=band_structure.as_dict(),
                nbands=band_structure.nb_bands,
                band_gap=band_structure.get_band_gap()["energy"],
                is_gap_direct=band_structure.get_band_gap()["direct"],
                band_gap_direct=band_structure.get_direct_band_gap(),
                energy_fermi=band_structure.efermi,
                conduction_band_minimum=band_structure.get_cbm()["energy"],
                valence_band_maximum=band_structure.get_vbm()["energy"],
                is_metal=band_structure.is_metal(),
            )
            if band_structure
            else {}
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return data if as_dict else cls(**data)


class BandStructureCalc(Structure, BandStructure, Calculation):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    base_info = BandStructure.base_info + Calculation.base_info

    def update_from_vasp_run(self, vasprun, corrections, directory):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.

        # All data analysis is done via a BandStructure object, so we convert
        # the vasprun object to that first.
        band_structure = vasprun.get_band_structure(line_mode=True)

        # Take our band_structure and expand its data for the rest of the columns.
        new_kwargs = BandStructure.from_toolkit(
            band_structure=band_structure,
            as_dict=True,
        )
        for key, value in new_kwargs.items():
            setattr(self, key, value)

        # lastly, we also want to save the corrections made and directory it ran in
        self.corrections = corrections
        self.directory = directory

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()
