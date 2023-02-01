# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.analysis.transition_state import NEBAnalysis
from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.apps.vasp.outputs import Vasprun
from simmate.database.base_data_types import Calculation, Structure, table_column
from simmate.toolkit import Structure as ToolkitStructure
from simmate.toolkit.diffusion import MigrationHop as ToolkitMigrationHop
from simmate.toolkit.diffusion import MigrationImages
from simmate.visualization.plotting import MatplotlibFigure


class DiffusionAnalysis(Structure, Calculation):
    class Meta:
        app_label = "workflows"

    api_filters = dict(
        migrating_specie=["exact"],
        vacancy_mode=["exact"],
        atomic_fraction=["range"],
        barrier_cell=["range"],
        npaths_involved=["range"],
    )

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
    def from_directory(cls, directory: Path):
        """
        Creates a new database entry from a directory that holds diffusion analysis
        results. For now, this assumes the directory holds vasp output files.
        """

        # I assume the directory is from a vasp calculation, but I need to update
        # this when I begin adding new apps.

        # For now, I only grab the structure from the static-energy and store
        # it in the DiffusionAnalysis table.
        found_dir = False
        for name in directory.iterdir():
            if name.is_dir() and name.stem.startswith("static-energy"):
                static_energy_dir = name
                found_dir = True
                break
        if not found_dir:
            raise Exception(
                "Unable to detect 'static-energy' directory and therefore unable "
                "to determine the bulk structure used for this analysis."
            )
            # TODO: try grabbing the bulk input structure from the metadata
            # file.

        bulk_filename = static_energy_dir / "POSCAR"
        bulk_structure = ToolkitStructure.from_file(bulk_filename)
        # BUG: I assume the directory location but this will fail if changed.

        # Save a diffusion analysis object so we can connect all other data
        # to it.
        analysis_db = cls.from_toolkit(
            structure=bulk_structure,
            vacancy_mode=True,  # assume this for now
        )
        analysis_db.save()

        # load the remaining data - such as migration hops
        analysis_db.update_from_directory(directory)

        return analysis_db

    def update_from_directory(self, directory: Path):
        # NOTE: This method is not called at the end of the workflow as
        # subflows often created the data already.

        # Iterate through all the subdirectories that start with "migration_hop*".
        # We also need to make sure we only grab directories because there are
        # also cifs present that match this naming convention.
        # We ignore the number when saving to avoid overwriting data.
        migration_directories = [
            f.absolute()
            for f in directory.iterdir()
            if f.is_dir() and "single-path" in f.stem
        ]

        # now save each migration hop present
        for migration_dir in migration_directories:
            hop = self.migration_hops.field.model.from_directory(
                directory=migration_dir,
            )
            hop.diffusion_analysis_id = self.id
            hop.save()


class MigrationHop(Calculation):
    class Meta:
        app_label = "workflows"

    archive_fields = [
        "site_start",
        "site_end",
        "index_start",
        "index_end",
        "number",
    ]

    api_filters = dict(
        site_start=["exact"],
        site_end=["exact"],
        number=["range"],
        length=["range"],
        dimension_path=["range"],
        dimension_host_lattice=["range"],
        energy_barrier=["range"],
    )

    # is_from_hop_obj = table_column.BooleanField(blank=True, null=True)
    # source = hop_obj / endpoints / images

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
    diffusion_analysis = table_column.ForeignKey(
        DiffusionAnalysis,
        on_delete=table_column.CASCADE,
        related_name="migration_hops",
        blank=True,
        null=True,
    )

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)
        self.write_neb_diagram_plot(directory=directory)
        self.write_migration_images(directory=directory)

    def get_migration_images(self) -> MigrationImages:
        structures = self.migration_images.order_by("number").to_toolkit()
        migration_images = MigrationImages(structures)
        return migration_images

    def write_migration_images(self, directory: Path):
        migration_images = self.get_migration_images()
        structure_sum = migration_images.get_sum_structure()
        structure_sum.to(
            filename=str(directory / "simmate_path_relaxed_neb.cif"),
            fmt="cif",
        )

    # TODO:
    # image_start --> OneToOneField for specific MigrationHop
    # image_end --> OneToOneField for specific MigrationHop
    # image_transition_state --> OneToOneField for specific MigrationHop

    # Just like Relaxation points to IonicSteps, NEB will point to MigrationImages

    # BUG: because of rounding in the from_toolkit method, the get_sc_structures
    # is unable to identify equivalent sites. I opened an issue for this
    # with their team:
    #   https://github.com/materialsvirtuallab/pymatgen-analysis-diffusion/issues/296
    def to_migration_hop_toolkit(self) -> ToolkitMigrationHop:
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

    def to_neb_toolkit(self) -> NEBAnalysis:
        images = self.migration_images.all()
        structures = self.migration_images.to_toolkit()

        neb_toolkit = NEBAnalysis(
            r=[i.structure_distance for i in images],
            energies=[i.energy for i in images],
            forces=[i.force_tangent for i in images],
            structures=structures,
        )
        return neb_toolkit

    def update_from_directory(self, directory: Path):
        # check if we have a VASP directory
        vasprun_filename = directory / "vasprun.xml"
        if not vasprun_filename.exists():
            raise Exception("Only VASP outputs are supported for NEB")

        from simmate.apps.vasp.outputs import Vasprun

        vasprun = Vasprun.from_directory(directory)
        self.update_from_neb_toolkit(vasprun)

    @classmethod
    def from_vasp_run(cls, vasprun: Vasprun, **kwargs):
        # BUG: the input here is actually already an NEBAnalysis
        # see the Vasprun.from_directory method
        return cls.from_neb_toolkit(neb_results=vasprun)

    @classmethod
    def from_neb_toolkit(cls, neb_results: NEBAnalysis):
        # This table entry will actually be completely empty... It only
        # serves to link the MigrationImages together. We only create this
        # if we are updating
        hop_db = cls()
        hop_db.save()

        # build out the images in the related table
        hop_db.update_from_neb_toolkit(neb_results)

        return hop_db

    def update_from_neb_toolkit(self, neb_results: NEBAnalysis):
        # build migration images and link them to this parent object.
        # Note, the start/end Migration images will exist already in the
        # relaxation database table. We still want to save them again here for
        # easy access.
        for image_number, image_data in enumerate(
            zip(
                neb_results.structures,
                neb_results.energies,
                neb_results.forces,
                neb_results.r,
            )
        ):
            image, energy, force, distance = image_data
            image_db = self.migration_images.field.model.from_toolkit(
                structure=image,
                number=image_number,
                force_tangent=force,
                energy=energy,
                structure_distance=distance,
                migration_hop_id=self.id,
            )
            image_db.save()

    @classmethod
    def from_toolkit(  # from_migration_hop_toolkit -- registration uses this
        cls,
        migration_hop: ToolkitMigrationHop = None,
        as_dict: bool = False,
        number: int = None,
        **kwargs,
    ):
        # the algorithm doesn't change for this method, but we do want to add
        # a few extra columns. Therefore we make the dictionary as normal and
        # then add those extra columns here.
        structure_dict = super().from_toolkit(as_dict=True, **kwargs)

        if migration_hop:
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
        else:
            hop_dict = {}

        all_data = {**structure_dict, **hop_dict}

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)


class MigrationImage(Structure):
    class Meta:
        app_label = "workflows"

    archive_fields = [
        "number",
        "force_tangent",
        "structure_distance",
        "energy",
    ]

    api_filters = dict(
        number=["exact"],
        force_tangent=["range"],
        energy=["range"],
        structure_distance=["range"],
    )

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

    migration_hop = table_column.ForeignKey(
        MigrationHop,
        on_delete=table_column.CASCADE,
        related_name="migration_images",
    )


class NebDiagram(MatplotlibFigure):
    def get_plot(results: MigrationHop):
        neb_results = results.to_neb_toolkit()
        plot = neb_results.get_plot()
        return plot


# register all plotting methods to the database table
for _plot in [NebDiagram]:
    _plot.register_to_class(MigrationHop)
