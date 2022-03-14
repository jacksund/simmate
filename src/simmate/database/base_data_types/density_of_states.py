# -*- coding: utf-8 -*-

"""
This module is experimental and subject to change.
"""

import os

from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.electronic_structure.plotter import DosPlotter

from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Calculation,
    Structure,
)


class DensityofStates(DatabaseTable):
    class Meta:
        abstract = True

    base_info = ["density_of_states_data"]

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

    def to_toolkit_density_of_states(self):
        return CompleteDos.from_dict(self.density_of_states_data)

    def get_densityofstates_plot(self):

        # DEV NOTE: Pymatgen only implements matplotlib for their band-structures
        # at the moment, but there are two scripts location elsewhere that can
        # outline how this can be done with Plotly:
        # https://plotly.com/python/v3/ipython-notebooks/density-of-states/
        # https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/components/bandstructure.py

        plotter = DosPlotter()
        complete_dos = self.to_toolkit_density_of_states()

        # Add the total density of States
        plotter.add_dos("Total DOS", complete_dos)

        # add element-projected density of states
        plotter.add_dos_dict(complete_dos.get_element_dos())

        # If I want plots for individual orbitals
        # for site in vasprun.final_structure:
        #     spd_dos = vasprun.complete_dos.get_site_spd_dos(site)
        #     plotter.add_dos_dict(spd_dos)

        # NOTE: get_dos_dict may be useful in the future

        plot = plotter.get_plot()
        return plot


class DensityofStatesCalc(Structure, DensityofStates, Calculation):
    class Meta:
        abstract = True
        app_label = "workflows"

    base_info = DensityofStates.base_info + Calculation.base_info

    def update_from_vasp_run(self, vasprun, corrections, directory):
        # Takes a pymatgen VaspRun object, which is what's typically returned
        # from a simmate VaspTask.run() call.

        # All data analysis is done via a CompleteDOS object, so we convert
        # the vasprun object to that first.
        density_of_states = vasprun.complete_dos

        # Take our dos and expand its data for the rest of the columns.
        new_kwargs = DensityofStates.from_toolkit(
            density_of_states=density_of_states,
            as_dict=True,
        )
        for key, value in new_kwargs.items():
            setattr(self, key, value)

        # lastly, we also want to save the corrections made and directory it ran in
        self.corrections = corrections
        self.directory = directory

        # Now we have the relaxation data all loaded and can save it to the database
        self.save()

    @classmethod
    def from_directory(cls, directory: str):
        # I assume the directory is from a vasp calculation, but I need to update
        # this when I begin adding new calculators.
        vasprun_filename = os.path.join(directory, "vasprun.xml")
        vasprun = Vasprun(vasprun_filename)
        density_of_states_db = cls.from_toolkit(
            structure=vasprun.structures[0],
            density_of_states=vasprun.complete_dos,
        )
        density_of_states_db.save()
        return density_of_states_db
