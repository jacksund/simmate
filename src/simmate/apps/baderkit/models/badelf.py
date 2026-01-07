# -*- coding: utf-8 -*-

from pathlib import Path

from baderkit.core import Badelf as BadelfClass

from simmate.database.base_data_types import (
    Calculation,
    Structure,
    table_column,
)
from simmate.apps.baderkit.models.elf_analysis import ElfAnalysis

class Badelf(Structure):
    """
    This table contains results from a BadELF analysis.
    """
    
    _analysis_model = ElfAnalysis
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this BadELF calculation
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    The oxidation states for each atom and electride in the system.
    """
    
    species = table_column.JSONField(blank=True, null=True)
    """
    The species in the structure.
    """
    
    labeled_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of chemical
    features in the system.
    """
    
    electride_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of quasi
    atoms (e.g. electrides, bare electrons, etc.)
    """

    charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom and electride
    feature in the system (i.e. electride/covelent bond etc.)
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of atom or electride volumes from the oxidation analysis
    """

    min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom or electride 
    to the bader/plane surface.
    """
    
    avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    A list of average distances from the origin of an atom or electride 
    to the bader/plane surface.
    """
    
    elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima for each atom and electride in the system.
    """
    
    electride_formula = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    The approximate formula for the structure including the electrides.
    The value is rounded to the nearest integer.
    """

    electrides_per_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    formula unit.
    """

    electrides_per_reduced_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    reduced formula unit.
    """

    nelectrides = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the maxima
    found using pybader.
    """

    electride_dimensionality = table_column.IntegerField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure.
    """
    
    all_electride_dims = table_column.JSONField(blank=True, null=True)
    """
    All dimensionalities the electride network has at varying ELF values
    in the system.
    """

    all_electride_dim_cutoffs = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality.
    """

    electride_structure = table_column.JSONField(blank=True, null=True)
    """
    A PyMatGen Structure JSON with dummy atoms (E) representing electrides.
    """

    elf_analysis = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="badelf",
        blank=True,
        null=True,
    )
    """
    The ElfAnalysis table entry from this calculation which includes
    more detailed information on each chemical feature found in the
    system.
    """
    
    total_charge = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    The value should match the total valence electrons used.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    total_volume = table_column.FloatField(blank=True, null=True)
    """
    The total volume of all atoms and electrides in the system.
    The value should match the total volume of the system.
    """
    
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    Which type of spin this calculation was performed on i.e. up, down, total, separate
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
    
    @classmethod
    def from_badelf(
            cls, 
            badelf: BadelfClass,
            directory: Path,
            **kwargs
            ):
        """
        Creates a new row from an Elfbadelf object
        """
        # get structure dict info
        structure_dict = cls._from_toolkit(
            structure=badelf.structure,
            as_dict=True
            )
        
        if (directory/"POTCAR").exists():
            badelf_dict = badelf.to_dict(directory / "POTCAR")
        else:
            badelf_dict = badelf.to_dict()
            
        results = {}
        model_columns = cls.get_column_names()
        for key in model_columns:
            # skip columns in the structure dict
            if key in structure_dict.keys():
                continue
            results[key] = badelf_dict.get(key, None)
            
        # create a new entry
        new_row = cls(
            **structure_dict,
            **results
            )
        new_row.save()

        # update elf features (unless it is updated elsewhere)
        if new_row.spin_system != "half":
            new_row.update_elf_analysis(badelf, directory)

        return new_row
                
    def update_elf_analysis(self, badelf: BadelfClass, directory: Path):
        # get the labeler model
        labeler_model = self._analysis_model
        # create a new entry
        labeler_entry = labeler_model.from_labeler(badelf.elf_labeler, directory=directory)
        # update key
        self.elf_analysis = labeler_entry
        self.save()
        
class BadelfCalculation(Calculation):
    """
    This table contains results from an ELF topology analysis calculation.
    The results should be from a dedicated workflow. 
    """
    class Meta:
        app_label = "baderkit"
    
    badelf = table_column.ForeignKey(
        "baderkit.Badelf",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )
    
    def update_from_badelf(self, badelf: BadelfClass, directory: Path, **kwargs):
        # create an entry in the ElfAnalysis table
        badelf = Badelf.from_badelf(badelf, directory, **kwargs)
        # link to table
        self.badelf = badelf
        self.save()