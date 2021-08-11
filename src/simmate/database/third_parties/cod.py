# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.structure import Structure


class CodStructure(Structure):
    
    # These fields overwrite the default Structure fields
    # BUG: We can't use CharField for the COD database because there are a number
    # of structures that have 20+ elements in them and are disordered. The disordered
    # aspect throws issues in pymatgen where formulas can be returned as long
    # floats (ex: Ca2.1234567N). Until this is fixed and cleaned up, I'll
    # need to use TextField instead of CharField for these fields.
    chemical_system = models.TextField()
    formula_full = models.TextField()
    formula_reduced = models.TextField()
    formula_anonymous = models.TextField()

    """ Base Info """

    # whether the structure contains disordered sites (i.e. mixed occupancies)
    is_ordered = models.BooleanField()
    
    # whether the structure has implicit Hydrogens. This means there should be
    # Hydrogens in the structure, but they weren't explicitly drawn.
    has_implicit_hydrogens = models.BooleanField()
    
    # Title of the paper that the structure is reported in
    # paper_title = models.CharField(blank=True, null=True)
    
    # Extra data by COD
    # See my notes in the scraping file. There's more metadata to add but I leave
    # this out for now.

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "COD"

    @property
    def external_link(self):
        # Links to the AFLOW dashboard for this structure. An example is...
        #   http://aflow.org/material/?id=aflow:ffea9279661c929f
        # !!! I could also consider an alternative link which points to an interactive
        # REST endpoint. The API is also sporatic for these, An example one is...
        #   aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/FCC/Dy1Mn2_ICSD_602151
        id_formatted = self.id.split("-")[-1]
        return f"http://www.crystallography.net/cod/{id_formatted}.html"
