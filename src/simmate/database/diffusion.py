# -*- coding: utf-8 -*-

from django.db import models

from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from pymatgen_diffusion.neb.pathfinder import MigrationPath

from simmate.database.base import Structure, Calculation


# --------------------------------------------------------------------------------------


class MaterialsProjectStructure(Structure):

    """ Base Info """

    # Materials Project ID
    # For now, max length of 12 is overkill: 'mp-123456789'
    id = models.CharField(max_length=12, primary_key=True)

    # Final calculated energy by Materials Project
    # Because Materials Project may be missing some of these values or we may add a
    # structure without a calc done, we set this column as optional.
    # TODO: should this be located in a Calculation relationship?
    final_energy = models.FloatField(blank=True, null=True)
    final_energy_per_atom = models.FloatField(blank=True, null=True)
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    e_above_hull = models.FloatField(blank=True, null=True)

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "Materials Project"

    """ Model Methods """

    # TODO: This should be an ETL workflow (maybe no L?). I can link to the
    # workflow in the future when it's ready
    # @classmethod
    # def from_query(criteria, api_key="2Tg7uUvaTAPHJQXl"):
    #     some_workflow.run()

    @classmethod
    def from_dict(cls, data_dict):
        # the dictionary format follows what is returned by the MPRester query,
        # which has requested the following properties:
        #   properties = [
        #       "material_id",
        #       "final_energy",
        #       "final_energy_per_atom",
        #       "formation_energy_per_atom",
        #       "e_above_hull",
        #       "structure",
        #   ]

        # For full compatibility with django, we need to rename the material_id
        # to just id. Also since I'm changing things in place, I need to make a
        # copy of the dict as well.
        data = data_dict.copy()
        data["id"] = data.pop("material_id")

        # initialize this model object using the data. I pass to super() method to
        # handle the "structure". The reason I even have this method is because
        # there's a bunch of extra kwargs I'm passing in along with "structure".
        structure_db = super().from_pymatgen(**data)

        return structure_db


# --------------------------------------------------------------------------------------


class Pathway(models.Model):

    """ Base info """

    # The element of the diffusion atom
    # Note: do not confuse this with ion, which has charge
    element = models.CharField(max_length=2)

    # the initial, midpoint, and end site fractional coordinates
    # Really, this is a list of float values, but I save it as a string.
    # !!! for robustness, should I save cartesian coordinates and/or lattice as well?
    # !!! Does the max length make sense here and below?
    # !!! Consider switch msite to image in the future.
    isite = models.CharField(max_length=100)
    msite = models.CharField(max_length=100)  # This belongs in Query-helper Info
    esite = models.CharField(max_length=100)

    # BUG: it really shouldn't be necessary to store these, but I need to for now
    # because of a bug (see to_pymatgen method below)
    iindex = models.IntegerField()
    eindex = models.IntegerField()

    """ Query-helper Info """

    # TODO:
    # The expected index in DistinctPathFinder.get_paths. The shortest path is index 0
    # and they are all ordered by increasing length
    # index is a reserved keyword so I need to use dpf_index
    # dpf_index = models.IntegerField()

    # The length/distance of the pathway from start to end (linear measurement)
    length = models.FloatField()

    # TODO:
    # Distance of the pathway relative to the shortest pathway distance
    # in the structure using the formula: (D - Dmin)/Dmin
    # distance_rel_min = models.FloatField()

    # atomic fraction of the diffusion ion
    atomic_fraction = models.FloatField()

    # Total number of sites in the structure unitcell and supercell sizes
    # NOTE: you can access nsites_unitcell via "self.structure.nsites"
    nsites_777 = models.IntegerField()
    nsites_101010 = models.IntegerField()
    nsites_121212 = models.IntegerField()

    """ Relationships """
    # Each Pathway corresponds to one Structure, which can have many Pathway(s)
    structure = models.ForeignKey(
        MaterialsProjectStructure,
        on_delete=models.CASCADE,
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
        # converts the django object to a pymatgen-diffusion MigrationPath

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

        path = MigrationPath(isite_new, esite_new, symm_structure)
        # BUG: the init script for MigrationPath can't identify the site indexes
        # properly but they should be the same as before because it is a symmetrized
        # structure. Note that even if I'm wrong in some case -- this will have
        # no effect because iindex and eindex are only used in one portion of
        # the hash as well as for printing the __str__ of the object.
        path.iindex = self.iindex
        path.eindex = self.eindex

        # if the pathways match, then we can return the pathway object!
        return path

    """ For website compatibility """

    class Meta:
        app_label = "diffusion"


# --------------------------------------------------------------------------------------


class EmpiricalMeasures(Calculation):

    """ Base info """

    # NOTE: these are actually separate calculations, but I think it's easiest
    # to have them all in the same table. I allow blank+null for all of them
    # just in case one of the individual calcs fail.

    # predicted oxidation state of the diffusing ion based on bond valence
    oxidation_state = models.IntegerField(blank=True, null=True)

    # Dimensionality of an individual pathway based on the Larsen Method
    dimensionality = models.IntegerField(blank=True, null=True)
    dimensionality_cumlengths = models.IntegerField(blank=True, null=True)

    # relative change in ewald_energy along the pathway: (Emax-Estart)/Estart
    ewald_energy = models.FloatField(blank=True, null=True)

    # relative change in ionic radii overlaps: (Rmax-Rstart)/Rstart
    ionic_radii_overlap_cations = models.FloatField(blank=True, null=True)
    ionic_radii_overlap_anions = models.FloatField(blank=True, null=True)

    """ Relationships """
    # Each PathwayCalcs corresponds to one Pathway, which can have many Pathway(s)
    # I set primary_key to true so that the primary keys match that of the pathway
    pathway = models.OneToOneField(Pathway, primary_key=True, on_delete=models.CASCADE)


# --------------------------------------------------------------------------------------
