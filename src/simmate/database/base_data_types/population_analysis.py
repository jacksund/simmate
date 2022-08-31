# -*- coding: utf-8 -*-

from pathlib import Path

from pandas import DataFrame
from pymatgen.io.vasp import Potcar
from pymatgen.io.vasp.outputs import Chgcar

from simmate.calculators.bader.outputs import ACF
from simmate.database.base_data_types import StaticEnergy, table_column


class PopulationAnalysis(StaticEnergy):
    """
    This table combines results from a static energy calculation and the follow-up
    oxidation analysis on the charge density.
    """

    class Meta:
        app_label = "workflows"

    exclude_from_summary = [
        "oxidation_states",
        "charges",
        "min_dists",
        "atomic_volumes",
        "element_list",
    ]

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states based on some analysis. This is 
    given back as a list of float values in the same order as sites in the
    source structure.
    """

    charges = table_column.JSONField(blank=True, null=True)

    min_dists = table_column.JSONField(blank=True, null=True)

    atomic_volumes = table_column.JSONField(blank=True, null=True)

    element_list = table_column.JSONField(blank=True, null=True)

    vacuum_charge = table_column.FloatField(blank=True, null=True)

    vacuum_volume = table_column.FloatField(blank=True, null=True)

    nelectrons = table_column.FloatField(blank=True, null=True)

    @classmethod
    def from_vasp_directory(cls, directory: Path, as_dict: bool = False):
        """
        A basic workup process that reads Bader analysis results from the ACF.dat
        file and calculates the corresponding oxidation states with the existing
        POTCAR files.
        """

        # For loading the static-energy data, we can just call the parent
        # method of this class.
        energy_data = StaticEnergy.from_vasp_directory(directory, as_dict=as_dict)

        # We must then look for the bader analysis data

        # load the ACF.dat file
        acf_filename = directory / "ACF.dat"
        dataframe, extra_data = ACF(filename=acf_filename)

        # !!! Consider moving this code to the Acf class

        # load the electron counts used by VASP from the POTCAR files
        # OPTIMIZE: this can be much faster if I have a reference file
        potcar_filename = directory / "POTCAR"
        potcars = Potcar.from_file(potcar_filename)
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})

        # SPECIAL CASE: in scenarios where empty atoms are added to the structure,
        # we should grab that modified structure instead of the one from the POSCAR.
        chgcar_filename = directory / "CHGCAR"
        chgcar_empty_filename = directory / "CHGCAR_empty"

        # the empty file will always take preference
        if chgcar_empty_filename.exists():
            chgcar = Chgcar.from_file(chgcar_empty_filename)
            structure = chgcar.structure
            # We typically use hydrogen ("H") as the empty atom, so we will
            # need to add this to our element list for oxidation analysis.
            # We use 0 for electron count because this is an 'empty' atom, and
            # not actually Hydrogen
            nelectron_data.update({"H": 0})

        # otherwise, grab the structure from the CHGCAR
        # OPTIMIZE: consider grabbing from the POSCAR or CONTCAR for speed
        else:
            chgcar = Chgcar.from_file(chgcar_filename)
            structure = chgcar.structure

        # Calculate the oxidation state of each site where it is simply the
        # change in number of electrons associated with it from vasp potcar vs
        # the bader charge I also add the element strings for filtering functionality
        elements = []
        oxi_state_data = []
        for site, site_charge in zip(structure, dataframe.charge.values):
            element_str = site.specie.name
            elements.append(element_str)
            oxi_state = nelectron_data[element_str] - site_charge
            oxi_state_data.append(oxi_state)

        # add the new column to the dataframe
        dataframe = dataframe.assign(
            oxidation_state=oxi_state_data,
            element=elements,
        )
        # !!! There are multiple ways to do this, but I don't know which is best
        # dataframe["oxidation_state"] = pandas.Series(
        #     oxi_state_data, index=dataframe.index)

        all_data = {
            # OPTIMIZE: consider a related table for Sites
            "oxidation_states": list(dataframe.oxidation_state.values),
            "charges": list(dataframe.charge.values),
            "min_dists": list(dataframe.min_dist.values),
            "atomic_volumes": list(dataframe.atomic_vol.values),
            "element_list": list(dataframe.element.values),
            **extra_data,
            **energy_data,
        }

        return all_data if as_dict else cls(**all_data)

    def get_summary_dataframe(self):
        # TODO
        pass
