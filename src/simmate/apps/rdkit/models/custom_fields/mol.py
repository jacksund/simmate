# -*- coding: utf-8 -*-

from django.db import models


class MolField(models.TextField):
    description = "The 'mol' data type of the RDkit extension"

    def db_type(self, connection):
        # gives the database column datatype
        return "mol"

    # OPTIMIZE: currently this field is stored as smiles strings when it would
    # be much faster to send the binary data to postgres AND recieve
    # binary data back.
    # Updates would include...
    #   1. changing the insert/save sql query to use "mol_from_pkl({value_binary})"
    #   2. changing the select sql query to use "mol_send"
    #   3. changing this class to a BinaryField as well (...?)
