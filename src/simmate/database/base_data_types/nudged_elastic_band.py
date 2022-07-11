# -*- coding: utf-8 -*-

"""
WARNING: This module is experimental and subject to change.
"""

import os

from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.transition_state import NEBAnalysis

from simmate.toolkit import Structure as ToolkitStructure
from simmate.toolkit.diffusion import MigrationHop as ToolkitMigrationHop
from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Structure,
)

# TODO: consider making a NestedCalculation
class DiffusionAnalysis(Structure):
    class Meta:
        abstract = True
        app_label = "workflows"

    migrating_specie = table_column.CharField(max_length=4, blank=True, null=True)
    """
    The element of the diffusion atom (e.g. "Li")
    """

    vacancy_mode = table_column.BooleanField(blank=True, null=True)
    """
    (if relevent) Whether vacancy or interstitial diffusion was used.
    """

    atomic_fraction = table_column.FloatField(blank=True, null=True)
    """
    Atomic fraction of the diffusion ion in the bulk structure.
    """

    # NOTE: barrier_cell, paths_involved, and npaths_involved need to be updated
    # by evaluating all MigrationHops.

    barrier_cell = table_column.FloatField(blank=True, null=True)
    """
    The energy barrier corresponding to the lowest-barrier percolation network
    """

    paths_involved = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The symmetrically-unqiue pathways involved in the lowest-barrier 
    percolation network. This is given as a list of IDs.
    """
    # TODO: consider making this a relationship to MigrationPathways

    npaths_involved = table_column.IntegerField(blank=True, null=True)
    """
    The number of symmetrically-unqiue pathways involved in the lowest-barrier 
    percolation network
    """

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
    def from_directory(cls, directory: str, **kwargs):
        """
        Creates a new database entry from a directory that holds diffusion analysis
        results. For now, this assumes the directory holds vasp output files.
        """

        # I assume the directory is from a vasp calculation, but I need to update
        # this when I begin adding new calculators.

        # TODO: It there a way I can figure out which tables the other calculations
        # are linked to? Specifically, the bulk relaxation, bulk static energy,
        # and the supercell relaxations. They are all in these directories too
        # but I can't save those results until I know where they belong.
        # Consider adding an attribute that points to those tables...? Or
        # maybe a relationship (which I'd rather avoid bc it makes things very
        # messy for users)
        # For now, I only grab the structure from the static-energy and store
        # it in the DiffusionAnalysis table.
        bulk_filename = os.path.join(
            directory,
            "static-energy.vasp.matproj",
            "POSCAR",
        )
        bulk_structure = ToolkitStructure.from_file(bulk_filename)

        # Save a diffusion analysis object so we can connect all other data
        # to it.
        analysis_db = cls.from_toolkit(
            structure=bulk_structure,
            vacancy_mode=True,  # assume this for now
        )
        analysis_db.save()

        # Iterate through all the subdirectories that start with "migration_hop*".
        # We also need to make sure we only grab directories because there are
        # also cifs present that match this naming convention.
        # We ignore the number when saving to avoid overwriting data.
        migration_directories = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, f))
            and f.startswith("migration_hop_")
        ]

        # now save each migration hop present
        for migration_dir in migration_directories:
            cls.migration_hops.field.model.from_directory(
                directory=migration_dir,
                diffusion_analysis_id=analysis_db.id,
            )

        return analysis_db

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

        #### Parameters

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

        #### Returns

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
        app_label = "workflows"

    base_info = [
        "site_start",
        "site_end",
        "index_start",
        "index_end",
        "number",
    ]

    # OPTIMIZE: site_start and site_end
    # Really, this is a list of float values, but I save it as a string.
    # For robustness, should I save cartesian coordinates and/or lattice as well?
    # Does the max length make sense here and below?
    # I could also store as JSON since it's a list of coords.

    site_start = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The starting fractional coordinates of the diffusing site.
    """

    site_end = table_column.CharField(max_length=100, blank=True, null=True)
    """
    The ending fractional coordinates of the diffusing site.
    """

    # BUG: the init script for MigrationHop can't identify the site indexes
    # properly but they should be the same as before because it is a symmetrized
    # structure. Note that even if I'm wrong in some case -- this will have
    # no effect because iindex and eindex are only used in one portion of
    # the hash as well as for printing the __str__ of the object.

    index_start = table_column.IntegerField(blank=True, null=True)
    """
    The starting site index of the diffusing site.
    """

    index_end = table_column.IntegerField(blank=True, null=True)
    """
    The ending site index of the diffusing site.
    """

    number = table_column.IntegerField(blank=True, null=True)
    """
    The expected index in DistinctPathFinder.get_paths. The shortest path is index 0
    and they are all ordered by increasing length.
    """

    length = table_column.FloatField(blank=True, null=True)
    """
    The length/distance of the pathway from start to end. Note, this is 
    linear measurement -- i.e. is it the length of the linear interpolated path.
    """

    dimension_path = table_column.IntegerField(blank=True, null=True)
    """
    The pathway dimensionality using the Larson scoring parameter.
    """

    dimension_host_lattice = table_column.IntegerField(blank=True, null=True)
    """
    Ignoring all atoms of the diffusing species, this is the dimensionality
    of the remaining atoms of the lattice using the Larson scoring parameter.
    """

    energy_barrier = table_column.FloatField(blank=True, null=True)
    """
    The energy barrier in eV. This evaluates all images of the diffusion pathway
    and find the difference between the maximum and minimum image energies.
    """

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
    def to_toolkit(self) -> ToolkitMigrationHop:
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

    #######
    # BUG: I need to distinguish between the from_toolkit/to_toolkit methods
    # above that just load a MigrationImages object vs. the from_directory and
    # from_pymatgen methods below that include results. As-is these similar
    # names but very different use cases makes things confusing for users.
    #######

    @classmethod
    def from_directory(cls, directory: str, **kwargs):
        # I assume the directory is from a vasp calculation, but I need to update
        # this when I begin adding new calculators.

        # BUG: A fix is make during the workup() method that may be relevant here.
        # simmate.calculators.vasp.tasks.nudged_elastic_band.MITNudgedElasticBand.workup
        analysis = NEBAnalysis.from_dir(directory)
        return cls.from_pymatgen(analysis=analysis, **kwargs)

    @classmethod
    def from_pymatgen(
        cls,
        analysis: NEBAnalysis,
        diffusion_analysis_id: int = None,  # only used if updating
        migration_hop_id: int = None,  # only used if updating
    ):
        # We reference these related tables frequently below so it easier to
        # grab them up front.
        diffusion_analysis_table = cls.diffusion_analysis.field.related_model
        migration_image_table = cls.migration_images.field.model

        # First, we need a migration_hop database object.
        # All of hops should link to a diffusion_analysis entry, so we check
        # for that here too. The key thing of these statements is that we
        # have a migration_hop_id at the end.

        # If no ids were given, then we make a new entries for each.
        if not diffusion_analysis_id and not migration_hop_id:
            # Note, we have minimal information if this is the case, so these
            # table entries will have a bunch of empty columns.

            # We don't have a bulk structure to use for this class, so we use
            # the first image
            analysis_db = diffusion_analysis_table.from_toolkit(
                structure=analysis.structures[0],
                vacancy_mode=True,  # assume this for now
            )
            analysis_db.save()

            # This table entry will actually be completely empty... It only
            # serves to link the MigrationImages together
            hop_db = cls(
                diffusion_analysis_id=analysis_db.id,
            )
            hop_db.save()
            migration_hop_id = hop_db.id

        elif diffusion_analysis_id and not migration_hop_id:
            # This table entry will actually be completely empty... It only
            # serves to link the MigrationImages together
            hop_db = cls(diffusion_analysis_id=diffusion_analysis_id)
            hop_db.save()
            migration_hop_id = hop_db.id

        elif migration_hop_id:
            # We don't use the hop_id, but making this query ensures it exists.
            hop_db = cls.objects.get(id=migration_hop_id)
            # Even though it's not required, we make sure the id given for the
            # diffusion analysis table matches this existing hop id.
            if diffusion_analysis_id:
                assert hop_db.diffusion_analysis.id == diffusion_analysis_id

        # Now same migration images and link them to this parent object.
        # Note, the start/end Migration images will exist already in the
        # relaxation database table. We still want to save them again here for
        # easy access.
        for image_number, image_data in enumerate(
            zip(
                analysis.structures,
                analysis.energies,
                analysis.forces,
                analysis.r,
            )
        ):
            image, energy, force, distance = image_data
            image_db = migration_image_table.from_toolkit(
                structure=image,
                number=image_number,
                force_tangent=force,
                energy=energy,
                structure_distance=distance,
                migration_hop_id=migration_hop_id,
            )
            image_db.save()

        return hop_db

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

        #### Parameters

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

        #### Returns

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
        app_label = "workflows"

    base_info = [
        "number",
        "structure_string",
        "force_tangent",
        "structure_distance",
        "energy",
    ]

    number = table_column.IntegerField()
    """
    The image number. Note, the starting image is always 0 and the ending
    image is always -1. The choice of -1 is because we often add the ending
    image to the database table before knowing how many midpoint images we
    are going to create.
    """

    force_tangent = table_column.FloatField(blank=True, null=True)
    """
    The tangent force of image. Not to be confused with forces from the Forces mix-in.
    """

    # Note, we only care about the total energy for NEB images -- not the other
    # fields that the Thermodynamics mix-in provides. This is why we set this
    # field directly, rather than using the mix-in.
    energy = table_column.FloatField(blank=True, null=True)
    """
    The calculated total energy. Units are in eV. 
    """

    structure_distance = table_column.FloatField(blank=True, null=True)
    """
    The fingerprint distance of the image from the starting image. A smaller
    means the structures are more similar, with 0 being an exact match.
    """

    # We don't need the source column for the MigrationImage class because we
    # instead stored the source on the DiffusionAnalysis object. This line
    # deletes the source column from our Structure mix-in.
    source = None

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

        #### Parameters

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

        #### Returns

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
