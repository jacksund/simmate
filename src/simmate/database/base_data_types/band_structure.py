# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.electronic_structure.bandstructure import (
    BandStructureSymmLine as ToolkitBandStructure,
)
from pymatgen.electronic_structure.plotter import BSPlotter
from pymatgen.io.vasp.outputs import Vasprun

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)
from simmate.visualization.plotting import MatplotlibFigure


class BandStructure(DatabaseTable):
    """
    The electronic band structure holds information about the range of energy
    levels that are available within a material.
    """

    class Meta:
        abstract = True

    exclude_from_summary = ["band_structure_data"]

    archive_fields = ["band_structure_data"]

    api_filters = dict(
        nbands=["range"],
        band_gap=["range"],
        band_gap_direct=["range"],
        is_gap_direct=["exact"],
        energy_fermi=["range"],
        conduction_band_minimum=["range"],
        valence_band_maximum=["range"],
        is_metal=["exact"],
    )

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

    def write_output_summary(self, directory: Path):
        """
        In addition to writing the normal VASP output summary, this also plots
        the bandstructure to "band_structure.png"
        """
        super().write_output_summary(directory)
        self.write_band_diagram_plot(directory=directory)

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


class BandStructureCalc(Structure, BandStructure, Calculation):
    """
    Holds Structure, BandStructure, and Calculation information. Band-structure
    workflows are common in materials science, so this table defines the most
    common data that results from such workflow calculations.
    """

    class Meta:
        app_label = "workflows"

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun, as_dict: bool = False):

        band_structure = vasprun.get_band_structure(line_mode=True)
        band_structure_db = cls.from_toolkit(
            structure=vasprun.structures[0],
            band_structure=band_structure,
            as_dict=as_dict,
        )
        if not as_dict:
            band_structure_db.save()
        return band_structure_db


class BandDiagram(MatplotlibFigure):
    def get_plot(result: BandStructure):

        # NOTE: This method should be moved to a toolkit object

        # DEV NOTE: Pymatgen only implements matplotlib for their band-structures
        # at the moment, but there are two scripts location elsewhere that can
        # outline how this can be done with Plotly:
        # https://plotly.com/python/v3/ipython-notebooks/density-of-states/
        # https://github.com/materialsproject/crystaltoolkit/blob/main/crystal_toolkit/components/bandstructure.py

        bs_plotter = BSPlotter(result.to_toolkit_band_structure())
        plot = bs_plotter.get_plot()
        return plot


# register all plotting methods to the database table
for _plot in [BandDiagram]:
    _plot.register_to_class(BandStructure)
