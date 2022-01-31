# -*- coding: utf-8 -*-

from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.toolkit.diffusion import MigrationHop
from simmate.database.base_data_types import (
    table_column,
    DatabaseTable,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)


class DiffusionAnalysis(DatabaseTable):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    barrier = table_column.FloatField()
    paths_involved = table_column.CharField(max_length=100, blank=True, null=True)
    npaths_involved = table_column.IntegerField(blank=True, null=True)
    structure = table_column.OneToOneField(
        "Structure",
        on_delete=table_column.PROTECT,
        primary_key=True,
        related_name="cell_barrier",
    )


class NudgedElasticBand(Calculation):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    # energy_start = table_column.FloatField(blank=True, null=True)
    # energy_end = table_column.FloatField(blank=True, null=True)
    # energy_max = table_column.FloatField(blank=True, null=True)
    # energy_min = table_column.FloatField(blank=True, null=True)

    energy_barrier = table_column.FloatField(blank=True, null=True)

    # OPTIONAL bc some calcs will be "from_endpoints" or "from_images"
    pathway = table_column.OneToOneField(
        "Pathway",
        on_delete=table_column.CASCADE,
    )

    # Just like Relaxation points to IonicSteps, NEB will point to MigrationImages


class MigrationImage(Structure, Thermodynamics, Forces):
    class Meta:
        abstract = True
        app_label = "local_calculations"


class Pathway(DatabaseTable):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    # The element of the diffusion atom
    # Note: do not confuse this with ion, which has charge
    element = table_column.CharField(max_length=2)

    # the initial, midpoint, and end site fractional coordinates
    # Really, this is a list of float values, but I save it as a string.
    # !!! for robustness, should I save cartesian coordinates and/or lattice as well?
    # !!! Does the max length make sense here and below?
    isite = table_column.CharField(max_length=100)
    esite = table_column.CharField(max_length=100)

    # pathway dimensionality
    dimension_path = table_column.IntegerField(blank=True, null=True)
    dimension_host_lattice = table_column.IntegerField(blank=True, null=True)

    """ Query-helper Info """

    # TODO:
    # The expected index in DistinctPathFinder.get_paths. The shortest path is index 0
    # and they are all ordered by increasing length
    # index is a reserved keyword so I need to use dpf_index
    # dpf_index = models.IntegerField()

    # The length/distance of the pathway from start to end (linear measurement)
    length = table_column.FloatField()

    # TODO:
    # Distance of the pathway relative to the shortest pathway distance
    # in the structure using the formula: (D - Dmin)/Dmin
    # distance_rel_min = models.FloatField()

    # atomic fraction of the diffusion ion
    atomic_fraction = table_column.FloatField()

    """ Relationships """
    # Each Pathway corresponds to one Structure, which can have many Pathway(s)
    structure = table_column.ForeignKey(
        # MaterialsProjectStructure,
        on_delete=table_column.CASCADE,
        related_name="pathways",
    )

    # Each Pathway will map to a row in the PathwayCalcs table. I keep this separate
    # for organization, though I could also move it here if I'd like

    """ Model Methods """
    # TODO: If I want a queryset to return a pymatgen-diffusion object(s) directly,
    # then I need make a new Manager rather than adding methods here.

    @classmethod
    def from_pymatgen(cls, path, structure_id):

        # In this table we store some extra info which we need to calculate first
        # iterate through supercell sizes and grab the nsites for each cell size
        min_superlattice_vectors = [7, 10, 12]
        nsites_supercells = []
        for min_sl_v in min_superlattice_vectors:
            supercell = path.symm_structure.copy()
            supercell_size = [
                (min_sl_v // length) + 1 for length in supercell.lattice.lengths
            ]
            supercell.make_supercell(supercell_size)
            nsites_supercells.append(supercell.num_sites)
        nsites_777, nsites_101010, nsites_121212 = nsites_supercells

        # convert the pathway object into the database table format
        pathway_db = cls(
            element=path.isite.specie,  # BUG: TODO: this should be element, not specie
            isite=" ".join(str(c) for c in path.isite.frac_coords),
            msite=" ".join(str(c) for c in path.msite.frac_coords),
            esite=" ".join(str(c) for c in path.esite.frac_coords),
            iindex=path.iindex,
            eindex=path.eindex,
            # dpf_index=path.dpf_index, # TODO
            length=path.length,
            # distance_rel_min = path.distance_rel_min, # TODO
            atomic_fraction=path.symm_structure.composition.get_atomic_fraction(
                path.isite.specie
            ),
            nsites_777=nsites_777,
            nsites_101010=nsites_101010,
            nsites_121212=nsites_121212,
            # OPTIMIZE: will this function still work if I only grab the pk value?
            # structure=MaterialsProjectStructure.objects.get(pk=structure_pk),
            structure_id=structure_id,
        )

        return pathway_db

    def to_pymatgen(self):
        # converts the django object to a pymatgen-diffusion MigrationHop

        # grab the related structure as a pymatgen object
        # OPTIMIZE: this makes an extra database query if structure isn't already
        # loaded. You can improve the efficiency of this call by having loaded
        # the self.structure.structure_json beforehand. You can do this with:
        #   path_db = Pathway.objects.get_related("structure__structure_json").get(id=1)
        structure = self.structure.to_pymatgen()

        # pathways require a symmetrized structure
        # BUG: I need to ensure the symmetrized structure comes out the same
        # as before, so I need to be careful with updates and hardcoding here.
        sga = SpacegroupAnalyzer(structure, symprec=0.1)
        symm_structure = sga.get_symmetrized_structure()

        isite_new = PeriodicSite(
            species=self.element,
            coords=[float(x) for x in self.isite.split(" ")],
            lattice=symm_structure.lattice,
        )
        esite_new = PeriodicSite(
            species=self.element,
            coords=[float(x) for x in self.esite.split(" ")],
            lattice=symm_structure.lattice,
        )

        path = MigrationHop(isite_new, esite_new, symm_structure)
        # BUG: the init script for MigrationPath can't identify the site indexes
        # properly but they should be the same as before because it is a symmetrized
        # structure. Note that even if I'm wrong in some case -- this will have
        # no effect because iindex and eindex are only used in one portion of
        # the hash as well as for printing the __str__ of the object.
        path.iindex = self.iindex
        path.eindex = self.eindex

        # if the pathways match, then we can return the pathway object!
        return path
