# -*- coding: utf-8 -*-

import json
from pathlib import Path

from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.electronic_structure.plotter import DosPlotter
from pymatgen.io.vasp.outputs import Vasprun

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)
from simmate.visualization.plotting import MatplotlibFigure


class DensityofStates(DatabaseTable):
    """
    The electronic density of states holds information about the range of energy
    levels that are available within a material.
    """

    class Meta:
        abstract = True

    exclude_from_summary = ["density_of_states_data"]

    archive_fields = ["density_of_states_data"]

    api_filters = dict(
        band_gap=["range"],
        energy_fermi=["range"],
        conduction_band_minimum=["range"],
        valence_band_maximum=["range"],
    )

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

    def write_output_summary(self, directory: Path):
        """
        In addition to writing the normal VASP output summary, this also plots
        the DOS to "density_of_states.png"
        """

        super().write_output_summary(directory)
        self.write_dos_diagram_plot(directory=directory)

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
                density_of_states_data=density_of_states.to_json(),
                band_gap=float(density_of_states.get_gap()),
                energy_fermi=density_of_states.efermi,
                conduction_band_minimum=float(density_of_states.get_cbm_vbm()[0]),
                valence_band_maximum=float(density_of_states.get_cbm_vbm()[1]),
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
        data = json.loads(self.density_of_states_data)
        return CompleteDos.from_dict(data)


class DensityofStatesCalc(Structure, DensityofStates, Calculation):
    """
    Holds Structure, DensityofStates, and Calculation information. Density of state
    workflows are common in materials science, so this table defines the most
    common data that results from such workflow calculations.
    """

    class Meta:
        app_label = "workflows"

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun, as_dict: bool = False):
        density_of_states_db = cls.from_toolkit(
            structure=vasprun.structures[0],
            density_of_states=vasprun.complete_dos,
            as_dict=as_dict,
        )
        if not as_dict:
            density_of_states_db.save()
        return density_of_states_db


class DosDiagram(MatplotlibFigure):
    def get_plot(result: DensityofStates):
        # NOTE: This method should be moved to a toolkit object

        # DEV NOTE: Pymatgen only implements matplotlib for their DOS
        # at the moment, but there are two scripts location elsewhere that can
        # outline how this can be done with Plotly:
        # https://plotly.com/python/v3/ipython-notebooks/density-of-states/
        # https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/components/bandstructure.py

        plotter = DosPlotter()
        complete_dos = result.to_toolkit_density_of_states()

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


# register all plotting methods to the database table
for _plot in [DosDiagram]:
    _plot.register_to_class(DensityofStates)
