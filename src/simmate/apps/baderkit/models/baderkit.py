# -*- coding: utf-8 -*-

from pathlib import Path
import logging

import numpy as np
from pandas import DataFrame

from simmate.database.base_data_types import Structure, Calculation, table_column

from baderkit.core import Bader

class BaderkitChargeAnalysis(Structure, Calculation):
    """
    This table contains results from a Bader charge analysis run using
    the BaderKit package.
    """

    html_display_name = "BaderKit Charge Analysis"
    html_description_short = "Results for BaderKit Charge Analysis Calculations"

    class Meta:
        app_label = "baderkit"

    exclude_from_summary = [
        "oxidation_states",
        "charges",
        "min_dists",
        "atomic_volumes",
        "element_list",
    ]

    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this Bader calculation
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each site.
    """

    atom_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each site.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    atom_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of site volumes from the oxidation analysis (i.e. the bader volume)
    """

    atom_min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The minimum distance from each atom to its partitioning surface.
    """    
    
    atom_avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The average distance from each atom to the points on its partitioning
    surface
    """
    
    basin_maxima_frac = table_column.JSONField(blank=True, null=True)
    """
    The fractional coordinates of each basin maximum
    """
    
    basin_maxima_charge_values = table_column.JSONField(blank=True, null=True)
    """
    The value of the charge density at each basin maximum
    """
    
    basin_maxima_ref_values = table_column.JSONField(blank=True, null=True)
    """
    The value of the reference grid at each basin maximum
    """
    
    basin_charges = table_column.JSONField(blank=True, null=True)
    """
    The charge associated with each bader basin.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation.
    """
    
    basin_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of basin volumes from the oxidation analysis (i.e. the bader volume)
    """

    basin_min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The minimum distance from each basin maximum to its partitioning surface.
    """    
    
    basin_avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The average distance from each basin maximum to the points on its partitioning
    surface
    """
    
    basin_atoms = table_column.JSONField(blank=True, null=True)
    """
    The atom site indices each basin is assigned to
    """
    
    basin_atom_dists = table_column.JSONField(blank=True, null=True)
    """
    The distance from each basin's maximum to the site it is assigned to
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

    total_electron_number = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)
        self.write_summary_dataframe(directory)

    def update_from_baderkit(self, bader: Bader, directory: Path):
        """
        A basic workup process that takes a BaderKit Bader class and
        reads the necessary data
        """
        # get structure dict info
        structure_dict = self._from_toolkit(
            structure=bader.structure,
            as_dict=True
            )
        
        data = {}
        # try and load each column in the table
        for entry in self.get_column_names():
            test_attr = getattr(bader, entry, None)
            # skip columns that we don't have a value for
            if test_attr is None:
                continue
            # convert numpy arrays
            if isinstance(test_attr, np.ndarray):
                test_attr = test_attr.tolist()
            data[entry] = test_attr
            
        # add extra data
        data["element_list"] = [i.specie.symbol for i in bader.structure]
        data["method_kwargs"] = dict(
            method = bader.method,
            vacuum_tol = bader.vacuum_tol,
            basin_tol = bader.basin_tol
            )
        # try to calculate oxidation states
        try:
            data["oxidation_states"] = bader.get_oxidation_from_potcar(directory / "POTCAR").tolist()
        except:
            logging.warning("No POTCAR found in file. Oxidation states will not be calculated")
        
        # update entry
        data.update(**structure_dict)
        self.update_from_fields(**data)
        self.save()

    def get_summary_dataframe(self):
        df = DataFrame(
            {
                "element": self.element_list,
                "oxidation_state": self.oxidation_states,
                "charge": self.atom_charges,
                "min_dist": self.atom_min_surface_distances,
                "atomic_volume": self.atom_volumes,
            }
        )
        return df

    def write_summary_dataframe(self, directory: Path):
        df = self.get_summary_dataframe()
        filename = directory / "simmate_population_summary.csv"
        df.to_csv(filename)
