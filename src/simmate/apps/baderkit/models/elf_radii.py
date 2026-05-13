# -*- coding: utf-8 -*-

from pathlib import Path
from simmate.database.base_data_types import DatabaseTable, table_column, Calculation

from baderkit.elf_analysis import ElfRadii as ElfRadiiClass


class ElfRadii(DatabaseTable):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """

    class Meta:
        app_label = "baderkit"

    site_index = table_column.IntegerField()
    """
    The index of the central atom that the radius is for
    """
    neigh_index = table_column.IntegerField()
    """
    The index of the neighboring atom
    """
    radius = table_column.FloatField()
    """
    The ELF ionic radius between the central atom and neighbor atom
    """
    site_frac_coords = table_column.JSONField()
    """
    The fractional coordinates of the first site
    """
    neigh_frac_coords = table_column.JSONField()
    """
    The fractional coordinates of the second site
    """
    radius_type = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of radius, i.e. covalent or ionic
    """
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The electron spin system this radius was calculated from. Options
    are:
        up - spin-up
        down - spin-down
        total - calculation not spin separate
        average - average of a spin separated system
    """
    
    @classmethod
    def from_baderkit(cls, elf_radii: ElfRadiiClass, directory: Path, **kwargs):
        """
        Creates a new row from an ElfLabeler object
        """
        # get structure dict info
        structure_dict = cls._from_toolkit(structure=elf_radii.structure, as_dict=True)

        results = {}
        model_columns = cls.get_column_names()
        for key in model_columns:
            # skip columns in the structure dict
            if key in structure_dict.keys():
                continue
            results[key] = getattr(elf_radii, key, None)

        # create a new entry
        new_row = cls(**structure_dict, **results)
        new_row.save()
        
        # update elf labeler
        new_row.update_elf_labeler(elf_radii)

        return new_row
    
    def update_elf_labeler(self, elf_radii: ElfRadiiClass):
        labeler = elf_radii.labeler

        # get radii info
        site_indices, neigh_indices, neigh_frac_coords, neigh_dists = (
            labeler.nearest_neighbor_data
        )
        site_frac_coords = labeler.structure.frac_coords[site_indices]
        radii = labeler.atom_nn_elf_radii
        bond_types = labeler.atom_nn_elf_radii_types
        # create radii entries
        for idx in range(len(site_indices)):
            radii_dict = dict(
                site_index=site_indices[idx],
                neigh_index=neigh_indices[idx],
                radius=radii[idx],
                site_frac_coords=site_frac_coords[idx].tolist(),
                neigh_frac_coords=neigh_frac_coords[idx].tolist(),
                radius_type=str(bond_types[idx]),
                spin_system=labeler.spin_system,
                analysis=self,
            )
            new_radii = ElfRadii(**radii_dict)
            new_radii.save()

class ElfRadiiCalculation(Calculation):
    """
    This table contains results from an ELF topology analysis calculation.
    The results should be from a dedicated workflow.
    """

    class Meta:
        app_label = "baderkit"

    analysis = table_column.ForeignKey(
        "baderkit.ElfRadii",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )

    def update_from_baderkit(self, radii: ElfRadii, directory: Path, **kwargs):
        # create an entry in the ElfAnalysis table
        radii = ElfRadii.from_baderkit(radii, directory)
        # link to table
        self.analysis = radii
        self.save()