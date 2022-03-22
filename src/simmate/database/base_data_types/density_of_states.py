# -*- coding: utf-8 -*-

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
    """
    The electronic density of states holds information about the range of energy
    levels that are available within a material.
    """

    class Meta:
        abstract = True

    base_info = ["density_of_states_data"]

    # !!! Consider breaking down data into...
    #   total
    #   elemental -- dict of ["total", "s", "p", "d", "f"], ["1", "-1"]
    #   orbital
    density_of_states_data = table_column.JSONField(blank=True, null=True)
    """
    A JSON dictionary holding all information for the band structure. This JSON
    is generated using pymatgen's `vasprun.complete_dos.as_dict()` and is 
    therefore currently unoptimized for small storage.
    """

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    energy_fermi = table_column.FloatField(blank=True, null=True)
    """
    The Fermi energy in eV.
    """

    conduction_band_minimum = table_column.FloatField(blank=True, null=True)
    """
    The conduction band minimum in eV.
    """

    valence_band_maximum = table_column.FloatField(blank=True, null=True)
    """
    The valence band maximum in eV.
    """

    # TODO: consider adding...
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

    def to_toolkit_density_of_states(self) -> CompleteDos:
        """
        Converts this DatabaseTable object into a toolkit CompleteDos, which
        has many more methods for plotting and analysis.
        """
        return CompleteDos.from_dict(self.density_of_states_data)

    def get_densityofstates_plot(self):
        """
        Plots the density of states using matplotlib
        """

        # NOTE: This method should be moved to a toolkit object

        # DEV NOTE: Pymatgen only implements matplotlib for their DOS
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
    """
    Holds Structure, DensityofStates, and Calculation information. Density of state
    workflows are common in materials science, so this table defines the most
    common data that results from such workflow calculations.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    base_info = Structure.base_info + DensityofStates.base_info + Calculation.base_info

    def update_from_vasp_run(self, vasprun: Vasprun, corrections: list, directory: str):
        """
        Given a pymatgen VaspRun object, which is what's typically returned
        from a simmate VaspTask.run() call, this will update the database entry
        with the results.
        """

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
        """
        Creates a new database entry from a directory that holds band-structure
        results. For now, this assumes the directory holds vasp output files.
        """

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
