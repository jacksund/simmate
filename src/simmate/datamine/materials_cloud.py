# -*- coding: utf-8 -*-

"""

This file is for pulling AFLOW data into the Simmate database. 

Materials Cloud looks to be composed of smaller databases, which makes this tricky.
After reading through their website, I don't see an easy way to access all of their
data. It does look like there is an easier OPTIMADE endpoint here though:
    https://www.optimade.org/providers-dashboard/providers/mcloud.html
OPTIMADE isn't super clear on how to query these subdatabases though. I need to 
do some more digging. I can get a single page of structures from this REST endpoint
though:
    https://aiida.materialscloud.org/3dd/optimade/structures
Read more at:
    https://petstore.swagger.io/?url=https://raw.githubusercontent.com/Materials-Consortia/OPTIMADE/v1.0.0/schemas/openapi_schema.json#/

Another option is using pymatgen's OPTIMADE class:
    https://github.com/materialsproject/pymatgen/blob/v2022.0.8/pymatgen/ext/optimade.py

"""
