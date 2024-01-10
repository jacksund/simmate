# -*- coding: utf-8 -*-

from pathlib import Path

from pandas import DataFrame

from simmate.database.base_data_types import Calculation, Structure, table_column


class BadElf(Structure, Calculation):
    """
    This table contains results from a BadELF analysis.
    """

    class Meta:
        app_label = "workflows"

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each site.
    """

    algorithm = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The selected algorithm. The default is BadELF as defined by the warren lab:
    https://pubs.acs.org/doi/10.1021/jacs.3c10876
    However, a more traditional Zero-flux surface type algorithm can be used as well.
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

    nelectrides = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the BCF.dat
    file in some BadELF or Bader workflows.
    """

    electride_dim = table_column.IntegerField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure. Defaults to
    the highest dimension network.
    """

    elf_connect_cutoff = table_column.FloatField(blank=True, null=True)
    """
    The ELF value cutoff used to determine if two electride sites are connected.
    Used to determine the dimensionality of the electride electron network.
    """

    coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms and electrides in the
    structure
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)
        self.write_summary_dataframe(directory)

    # def from_vasp_run(vasprun, as_dict):
    #     """
    #     The base workflow class will register the vasprun.xml and try and load
    #     vasp data using a from_vasp_run method. We don't actually want to load
    #     anything so this method just passes.
    #     """
    #     pass
    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass

    def get_summary_dataframe(self):
        """
        Creates a dataframe containing the information that is most likely to
        be useful to a user.
        """
        df = DataFrame(
            {
                "element": self.element_list,
                "oxidation_state": self.oxidation_states,
                "charge": self.charges,
                "min_dist": self.min_dists,
                "atomic_volume": self.atomic_volumes,
                "nelectrons": self.nelectrons,
                "nelectrides": self.nelectrides,
                "electride_dim": self.electride_dim,
            }
        )
        return df

    def write_summary_dataframe(self, directory: Path):
        """
        writes the summary dataframe from above to a csv file.
        """
        df = self.get_summary_dataframe()
        filename = directory / "badelf_summary.csv"
        df.to_csv(filename)
