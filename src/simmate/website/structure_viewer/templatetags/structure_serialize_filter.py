# -*- coding: utf-8 -*-

# For adding new filters to django, look at...
# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/

import urllib

from django import template
from django.utils.safestring import mark_safe

from simmate.toolkit import Structure

# We need a registration instance in order to configure everything with Django
register = template.Library()


@register.filter(name="structure_url")
def structure_to_url(structure: Structure):
    """
    Converts a toolkit Structure to a URL GET query. For example, a structure
    would return "?structure_string='...'". This is useful for when we want
    to pass a crystal structure directly from a URL -- which is what is 
    done for our crystal structure viewer.
    """
    
    # !!! This code should be located within a method on the toolkit class
    storage_format = "POSCAR" if structure.is_ordered else "CIF"
    structure_string=structure.to(fmt=storage_format)
    # !!!
    
    # Take the output and convert it a URL query format
    url_query = urllib.parse.urlencode(dict(structure_string=structure_string))

    # Because we added new html to our script, we need to have Django check it
    # ensure it safe before returning. Read more about this here:
    # https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#filters-and-auto-escaping
    return mark_safe(url_query)
