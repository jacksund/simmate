# -*- coding: utf-8 -*-

from pathlib import Path

from pandas import DataFrame
from simmate.database.base_data_types import StaticEnergy, table_column

from simmate.apps.warrenapp.badelf_tools.acf import ACF
from simmate.apps.warrenapp.badelf_tools.utilities import get_electride_num


class WarrenPopulationAnalysis(StaticEnergy):
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
    A list of calculated oxidation states for each site.
    """

    charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each site.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    min_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum radii distance for bader volumes. i.e. the minimum
    distance from the origin of the site to the bader surface. This can be used
    as a minimum radius for the site.
    """

    atomic_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of site volumes from the oxidation analysis (i.e. the bader volume)
    """

    element_list = table_column.JSONField(blank=True, null=True)
    """
    A list of all element species in order that appear in the structure.
    
    This information is stored in the 'structure' column as well, but it is 
    stored here as an extra for convenience.
    """

    vacuum_charge = table_column.FloatField(blank=True, null=True)
    """
    Total electron count that was NOT assigned to ANY site -- and therefore
    assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    vacuum_volume = table_column.FloatField(blank=True, null=True)
    """
    Total volume from electron density that was NOT assigned to ANY site -- 
    and therefore assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    nelectrons = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    nelectrides = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the BCF.dat
    file in some BadELF or Bader workflows.
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)
        self.write_summary_dataframe(directory)

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
        dataframe, extra_data = ACF(directory)

        # get the number of electrides
        try:
            num_electrides = get_electride_num(directory)
        except:
            num_electrides = 0
        all_data = {
            # OPTIMIZE: consider a related table for Sites
            "oxidation_states": list(dataframe.oxidation_state.values),
            "charges": list(dataframe.charge.values),
            "min_dists": list(dataframe.min_dist.values),
            "atomic_volumes": list(dataframe.atomic_vol.values),
            "element_list": list(dataframe.element.values),
            "nelectrides": num_electrides,
            **extra_data,
            **energy_data,
        }

        return all_data if as_dict else cls(**all_data)

    def get_summary_dataframe(self):
        df = DataFrame(
            {
                "element": self.element_list,
                "oxidation_state": self.oxidation_states,
                "charge": self.charges,
                "min_dist": self.min_dists,
                "atomic_volume": self.atomic_volumes,
                "nelectrides": self.nelectrides,
            }
        )
        return df

    def write_summary_dataframe(self, directory: Path):
        df = self.get_summary_dataframe()
        filename = directory / "simmate_population_summary.csv"
        df.to_csv(filename, index=False)
