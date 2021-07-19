# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.base import Structure


class CodStructure(Structure):

    """ Base Info """

    # COD ID
    # For now, max length of 14 is overkill: 'ocd-123456789'
    id = models.CharField(max_length=14, primary_key=True)
    
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
