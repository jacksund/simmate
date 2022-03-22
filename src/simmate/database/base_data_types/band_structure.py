# -*- coding: utf-8 -*-

import os

from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.bandstructure import (
    BandStructureSymmLine as ToolkitBandStructure,
)
from pymatgen.electronic_structure.plotter import BSPlotter

from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Calculation,
    Structure,
)


class BandStructure(DatabaseTable):
    """
    The electronic band structure holds information about the range of energy
    levels that are available within a material.
    """

    class Meta:
        abstract = True

    base_info = ["band_structure_data"]

    # kpt_path_type (setyawan_curtarolo, hinuma, latimer_munro)
    # Maybe set as an abstract property?

    band_structure_data = table_column.JSONField(blank=True, null=True)
    """
    A JSON dictionary holding all information for the band structure. This JSON
    is generated using pymatgen's 
    `vasprun.get_band_structure(line_mode=True).as_dict()` and is therefore
    currently unoptimized for small storage.
    """

    nbands = table_column.IntegerField(blank=True, null=True)
    """
    The number of bands used in this calculation.
    """

    band_gap = table_column.FloatField(blank=True, null=True)
    """
    The band gap energy in eV.
    """

    is_gap_direct = table_column.BooleanField(blank=True, null=True)
    """
    Whether the band gap is direct or indirect.
    """

    band_gap_direct = table_column.FloatField(blank=True, null=True)
    """
    The direct band gap energy in eV.
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

    is_metal = table_column.BooleanField(blank=True, null=True)
    """
    Whether the material is a metal.
    """

    # TODO: consider adding...
    # magnetic_ordering (Magnetic ordering of the calculation.)
    # equivalent_labels (Equivalent k-point labels in other k-path conventions)

    @classmethod
    def _from_toolkit(
        cls,
        band_structure: ToolkitBandStructure = None,
        as_dict: bool = False,
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

    def to_toolkit_band_structure(self) -> ToolkitBandStructure:
        """
        Converts this DatabaseTable object into a toolkit BandStructure, which
        has many more methods for plotting and analysis.
        """
        return ToolkitBandStructure.from_dict(self.band_structure_data)

    def get_bandstructure_plot(self):  # -> matplotlib figure
        """
        Plots the band structure using matplotlib
        """

        # NOTE: This method should be moved to a toolkit object

        # DEV NOTE: Pymatgen only implements matplotlib for their band-structures
        # at the moment, but there are two scripts location elsewhere that can
        # outline how this can be done with Plotly:
        # https://plotly.com/python/v3/ipython-notebooks/density-of-states/
        # https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/components/bandstructure.py

        bs_plotter = BSPlotter(self.to_toolkit_band_structure())
        plot = bs_plotter.get_plot()
        return plot


class BandStructureCalc(Structure, BandStructure, Calculation):
    """
    Holds Structure, BandStructure, and Calculation information. Band-structure
    workflows are common in materials science, so this table defines the most
    common data that results from such workflow calculations.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    base_info = Structure.base_info + BandStructure.base_info + Calculation.base_info

    def update_from_vasp_run(
        self,
        vasprun: Vasprun,
        corrections: list,
        directory: str,
    ):
        """
        Given a pymatgen VaspRun object, which is what's typically returned
        from a simmate VaspTask.run() call, this will update the database entry
        with the results.
        """

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
        band_structure = vasprun.get_band_structure(line_mode=True)
        band_structure_db = cls.from_toolkit(
            structure=vasprun.structures[0],
            band_structure=band_structure,
        )
        band_structure_db.save()
        return band_structure_db
