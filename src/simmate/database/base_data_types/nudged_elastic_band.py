# -*- coding: utf-8 -*-

"""
This module is experimental and subject to change.
"""


from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.toolkit.diffusion import MigrationHop as ToolkitMigrationHop
from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Structure,
)


class DiffusionAnalysis(Structure):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    # The element of the diffusion atom
    migrating_specie = table_column.CharField(max_length=4, blank=True, null=True)

    # Whether vacancy or interstitial diffusion was used
    vacancy_mode = table_column.BooleanField(blank=True, null=True)

    # atomic fraction of the diffusion ion
    atomic_fraction = table_column.FloatField(blank=True, null=True)

    # Evaluates all MigrationHops to find the lowest-barrier percolation network
    barrier_cell = table_column.FloatField(blank=True, null=True)
    paths_involved = table_column.CharField(max_length=100, blank=True, null=True)
    npaths_involved = table_column.IntegerField(blank=True, null=True)

    @classmethod
    def from_toolkit(
        cls,
        migrating_specie: str = None,
        vacancy_mode: bool = None,
        as_dict: bool = False,
        **kwargs,
    ):
        # the algorithm doesn't change for this method, but we do want to add
        # a few extra columns. Therefore we make the dictionary as normal and
        # then add those extra columns here.
        structure_dict = super().from_toolkit(as_dict=True, **kwargs)

        # now add the two extra columns
        structure_dict["migrating_specie"] = migrating_specie
        # Structure should be present -- otherwise an error would have been
        # raised by the call to super()
        structure_dict["atomic_fraction"] = (
            kwargs["structure"].composition.get_atomic_fraction(migrating_specie)
            if migrating_specie
            else None
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return structure_dict if as_dict else cls(**structure_dict)

    @classmethod
    def create_subclasses(
        cls,
        name: str,
        module: str,
        **extra_columns,
    ):
        """
        Dynamically creates a subclass of Relaxation as well as a separate IonicStep
        table for it. These tables are linked together.

        Example use:

        ``` python
        from simmate.database.base_data_types import Relaxation

        # note the odd formatting here is just because we are parsing three
        # outputs from this method to three variables.
        (
            ExampleDiffusionAnalysis,
            ExampleMigrationHop,
            ExampleMigrationImage,
        ) = DiffusionAnalysis.create_subclasses(
            "Example",
            module=__name__,
        )
        ```

        Parameters
        ----------
        - `name` :
            The prefix name of the subclasses that are output. "Relaxation" and
            "IonicStep" will be attached to the end of this prefix.

        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.

        - `**extra_columns` :
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        Returns
        -------
        - `NewDiffusionAnalysisClass` :
            A subclass of DiffusionAnalysis.
        - `NewMigrationHopClass`:
            A subclass of MigrationHop.
        - `NewMigrationHopClass`:
            A subclass of MigrationHop.
        """

        # For convience, we add columns that point to the start and end structures
        NewDiffusionAnalysisClass = cls.create_subclass(
            f"{name}DiffusionAnalysis",
            module=module,
            **extra_columns,
        )

        (
            NewMigrationHopClass,
            NewMigrationImageClass,
        ) = MigrationHop.create_subclasses_from_diffusion_analysis(
            name,
            NewDiffusionAnalysisClass,
            module=module,
            **extra_columns,
        )

        # we now have a new child class and avoided writing some boilerplate code!
        return NewDiffusionAnalysisClass, NewMigrationHopClass, NewMigrationImageClass


# TODO: consider making a Calculation bc this is what the corrections/directory
# information should be attached to.
class MigrationHop(DatabaseTable):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    # the initial, midpoint, and end site fractional coordinates
    # Really, this is a list of float values, but I save it as a string.
    # !!! for robustness, should I save cartesian coordinates and/or lattice as well?
    # !!! Does the max length make sense here and below?
    # !!! I could also store as JSON since it's a list of coords.
    site_start = table_column.CharField(max_length=100, blank=True, null=True)
    site_end = table_column.CharField(max_length=100, blank=True, null=True)

    # BUG: the init script for MigrationHop can't identify the site indexes
    # properly but they should be the same as before because it is a symmetrized
    # structure. Note that even if I'm wrong in some case -- this will have
    # no effect because iindex and eindex are only used in one portion of
    # the hash as well as for printing the __str__ of the object.
    index_start = table_column.IntegerField(blank=True, null=True)
    index_end = table_column.IntegerField(blank=True, null=True)

    """ Query-helper Info """

    # TODO:
    # The expected index in DistinctPathFinder.get_paths. The shortest path is index 0
    # and they are all ordered by increasing length.
    number = table_column.IntegerField(blank=True, null=True)

    # The length/distance of the pathway from start to end (linear measurement)
    length = table_column.FloatField(blank=True, null=True)

    # pathway dimensionality
    dimension_path = table_column.IntegerField(blank=True, null=True)
    dimension_host_lattice = table_column.IntegerField(blank=True, null=True)

    # Evaluates all MigrationImages to find the barriers
    energy_barrier = table_column.FloatField(blank=True, null=True)

    # TODO:
    # Distance of the pathway relative to the shortest pathway distance
    # in the structure using the formula: (D - Dmin)/Dmin
    # distance_rel_min = models.FloatField()

    """ Relationships """
    # Each MigrationHop corresponds to the full analysis of one Structure, which
    # can have many MigrationHop(s)
    # diffusion_analysis = table_column.ForeignKey(
    #     # DiffusionAnalysis,
    #     on_delete=table_column.PROTECT,
    #     related_name="migration_hops",
    # )

    # TODO:
    # image_start --> OneToOneField for specific MigrationHop
    # image_end --> OneToOneField for specific MigrationHop
    # image_transition_state --> OneToOneField for specific MigrationHop

    # Just like Relaxation points to IonicSteps, NEB will point to MigrationImages

    """ Model Methods """
    # TODO: If I want a queryset to return a pymatgen-diffusion object(s) directly,
    # then I need make a new Manager rather than adding methods here.

    @classmethod
    def _from_toolkit(
        cls,
        migration_hop: ToolkitMigrationHop,
        as_dict: bool = False,
        number: int = None,
        **kwargs,
    ):

        # convert the pathway object into the database table format
        hop_dict = dict(
            site_start=" ".join(str(c) for c in migration_hop.isite.frac_coords),
            site_end=" ".join(str(c) for c in migration_hop.esite.frac_coords),
            index_start=migration_hop.iindex,
            index_end=migration_hop.eindex,
            length=migration_hop.length,
            # diffusion_analysis_id=diffusion_analysis_id,
            **kwargs,
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return hop_dict if as_dict else cls(**hop_dict)

    # BUG: because of rounding in the from_toolkit method, the get_sc_structures
    # is unable to identify equivalent sites. I opened an issue for this
    # with their team:
    #   https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/issues/296
    def to_toolkit(self):
        """
        converts the database MigrationHop to a toolkit MigrationHop
        """
        # The bulk crystal structure is stored in the diffusion analysis table
        structure = self.diffusion_analysis.to_toolkit()

        # pathways require a symmetrized structure
        # BUG: I need to ensure the symmetrized structure comes out the same
        # as before, so I need to be careful with updates and hardcoding here.
        sga = SpacegroupAnalyzer(structure, symprec=0.1)
        symm_structure = sga.get_symmetrized_structure()

        isite_new = PeriodicSite(
            species=self.diffusion_analysis.migrating_specie,
            coords=[float(x) for x in self.site_start.split(" ")],
            lattice=symm_structure.lattice,
        )
        esite_new = PeriodicSite(
            species=self.diffusion_analysis.migrating_specie,
            coords=[float(x) for x in self.site_end.split(" ")],
            lattice=symm_structure.lattice,
        )

        path = ToolkitMigrationHop(isite_new, esite_new, symm_structure)
        # BUG: see comment attached to definition of these fields
        path.iindex = self.index_start
        path.eindex = self.index_end

        # if the pathways match, then we can return the pathway object!
        return path

    @classmethod
    def create_subclasses_from_diffusion_analysis(
        cls,
        name: str,
        diffusion_analysis: DiffusionAnalysis,
        module: str,
        **extra_columns,
    ):
        """
        Dynamically creates subclass of MigrationHop and MigrationImage, then
        links them to the DiffusionAnalysis table.

        This method should NOT be called directly because it is instead used by
        `DiffusionAnalysis.create_subclasses`.

        Parameters
        ----------
        - `name` :
            Name of the subclass that is output.
        - `diffusion_analysis` :
            DiffusionAnalysis table that these subclasses should be associated with.
        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.
        - `**extra_columns` :
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        Returns
        -------
        - `NewMigrationHopClass`:
            A subclass of MigrationHop.
        - `NewMigrationHopClass`:
            A subclass of MigrationHop.
        """

        NewMigrationHopClass = cls.create_subclass(
            f"{name}MigrationHop",
            diffusion_analysis=table_column.ForeignKey(
                diffusion_analysis,
                on_delete=table_column.CASCADE,
                related_name="migration_hops",
            ),
            module=module,
            **extra_columns,
        )

        NewMigrationImageClass = MigrationImage.create_subclass_from_migration_hop(
            name,
            NewMigrationHopClass,
            module=module,
            **extra_columns,
        )

        return NewMigrationHopClass, NewMigrationImageClass


class MigrationImage(Structure):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    base_info = [
        "number",
        "structure_string",
        "force_tangent",
        "structure_distance",
        "energy",
    ]

    # 0 = start, -1 = end.
    number = table_column.IntegerField()

    # Diffusion analysis given a tangent force, so we don't mix this up with the
    # Force mix-in.
    force_tangent = table_column.FloatField(blank=True, null=True)

    # For NEB, we only care about the total energy -- not the other fields that
    # the Thermodynamics mix-in provides.
    energy = table_column.FloatField(blank=True, null=True)

    # This measures the fingerprint distance of the image from the starting image
    structure_distance = table_column.FloatField(blank=True, null=True)

    # We don't need the source column for the MigrationImage class because we
    # instead stored on the DiffusionAnalysis object. This line deletes the
    # source could from our Structure mix-in.
    source = None

    def update_many_from_analysis(self):
        # StaticEnergy.update_from_vasp_run but adjusted to load a NEB vasprun
        pass

    @classmethod
    def create_subclass_from_migration_hop(
        cls,
        name: str,
        migration_hop: MigrationHop,
        module: str,
        **extra_columns,
    ):
        """
        Dynamically creates subclass of MigrationImage, then links it to the
        MigrationHop table.

        This method should NOT be called directly because it is instead used by
        `DiffusionAnalysis.create_subclasses`.

        Parameters
        ----------
        - `name` :
            Name of the subclass that is output.
        - `migration_hop` :
            MigrationHop table that these images should be associated with.
        - `module` :
            name of the module this subclass should be associated with. Typically,
            you should pass __name__ to this.
        - `**extra_columns` :
            Additional columns to add to the table. The keyword will be the
            column name and the value should match django options
            (e.g. table_column.FloatField())

        Returns
        -------
        - `NewClass` :
            A subclass of MigrationImage.

        """

        NewClass = cls.create_subclass(
            f"{name}MigrationImage",
            migration_hop=table_column.ForeignKey(
                migration_hop,
                on_delete=table_column.CASCADE,
                related_name="migration_images",
            ),
            module=module,
            **extra_columns,
        )

        return NewClass
