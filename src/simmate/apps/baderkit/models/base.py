 # -*- coding: utf-8 -*-

from pathlib import Path
import re

import numpy as np

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column
    )

class BaderkitBase(DatabaseTable):
    """
    This is an abstract table that other BaderKit tables inhereit from. It defines
    the basic outline of updating each table.
    """
    
    _local_tables = []
    
    class Meta:
        abstract = True
        
    structure = table_column.ForeignKey(
        "baderkit.Baderkit",
        on_delete=table_column.CASCADE,
        related_name="%(class)s",
        blank=True,
        null=True,
    )
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this BaderKit calculation.
    """


    @classmethod
    def from_baderkit(cls, structure_entry, baderkit_class, directory: Path, sub_entries = [], sub_entry_names = [], **kwargs):
        """
        A basic workup process that takes a BaderKit Bader class and
        reads the necessary data
        """
        
        # Get results from this class
        results_dict = baderkit_class.to_dict(serializable=True)
        
        # create dict to store results for model columns
        data = {
            "structure" : structure_entry,
            "method_kwargs" : results_dict.get("method_kwargs")
            }
        # try and load each column in the table
        for entry in cls.get_column_names():
            # BaderKit's summary dict has a nested structure. The keys in the
            # first layer are not consistent and are meant for human readability,
            # so we can just loop over them and search for our desired entry.
            for _, sub_dict in results_dict.items():
                test_attr = results_dict.get(entry, None)
                # If we don't have a result, skip
                if test_attr is None:
                    continue
                data[entry] = test_attr
                break

        # create new entry
        new_entry = cls(**data)
        new_entry.save()
        
        # if there are sub table that connect to this one, we connect them here
        if cls._local_tables:
            entry_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
            for table in cls._local_tables:
                table.from_baderkit(
                    parent_entry=new_entry,
                    parent_name=entry_name,
                    baderkit_class=baderkit_class,
                    directory=directory,
                    **kwargs
                    )

        return new_entry

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
    
class BaderkitLocalBase(DatabaseTable):
    """
    This is an abstract table for tables that hold data on local structure rather
    than the full structure (e.g. radii, elf basins, etc.)
    """
    range_attribute = None
    
    class Meta:
        abstract = True

    @classmethod
    def from_baderkit(
            cls, 
            parent_entry,
            parent_name,
            baderkit_class, 
            directory: Path, 
            **kwargs,
            ):
        """
        A basic workup process that takes a BaderKit Bader class and
        reads the necessary data
        """
        
        # create dict to store results for model columns
        
        results_dict = baderkit_class.to_dict(serializable=True)
        new_entries = []
        
        model_columns = cls.get_column_names()
        
        for i in range(len(getattr(baderkit_class, cls.range_attribute))):
            # link to parent
            results = {
                parent_name : parent_entry,
                }
            for key in model_columns:
                for subdict in results_dict.values():
                    test_attr = subdict.get(key, None)
                    if test_attr is not None:
                        results[key] = test_attr[i]
                        break
    
            # create a new entry
            new_row = cls(**results)
            new_row.save()
            
            new_entries.append(new_row)
            
        return new_entries

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
    
class Baderkit(Structure, Calculation):
    """
    This is the base class that all baderkit models link to. This is designed
    so that results from the same ab-initio calculation are linked to each
    other by this central source.
    """
    
    class Meta:
        app_label = "baderkit"
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this BaderKit calculation.
    """
    
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The electron spin system this radius was calculated from. Options
    are:
        up - spin-up
        down - spin-down
        not polarized - calculation not spin polarized
    """
    
    species = table_column.JSONField(blank=True, null=True)
    """
    A list of all element species in order that appear in the structure.
    
    This information is stored in the 'structure' column as well, but it is 
    stored here as an extra for convenience.
    """
    
    valence_counts = table_column.JSONField(blank=True, null=True)
    """
    The valence counts from the pseudopotentials used for this calculation.
    """
    
    vacuum_charge = table_column.FloatField(blank=True, null=True)
    """
    Total electron count that was NOT assigned to ANY site -- and therefore
    assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    vacuum_volume = table_column.FloatField(blank=True, null=True)
    """
    Total volume from electron density that was NOT assigned to ANY site -- 
    and therefore assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    def update_from_baderkit(
            self, 
            baderkit_objects,
            directory: Path, 
            **kwargs,
            ):
        
        # get results from the first object
        # Get results from this class
        results_dict = baderkit_objects[0].to_dict(serializable=True)
        
        # create dict to store results for model columns
        data = {}
        # try and load each column in the table
        for entry in self.get_column_names():
            # BaderKit's summary dict has a nested structure. The keys in the
            # first layer are not consistent and are meant for human readability,
            # so we can just loop over them and search for our desired entry.
            for _, sub_dict in results_dict.items():
                test_attr = results_dict.get(entry, None)
                # If we don't have a result, skip
                if test_attr is None:
                    continue
                data[entry] = test_attr
                break
        
        
        all_kwargs = {}
        
        for baderkit_object in baderkit_objects:
            all_kwargs.update(baderkit_object._get_kwargs())
            # get the name of this objects class
            object_name = baderkit_object.__class__.__name__
            # get the name of the table entry for this class
            entry_name = object_name.lower()
            # get the model to save to
            model_object = getattr(self, entry_name)
            if model_object is None:
                continue
            model = model_object.model
            # create a new entry
            entry = model.from_baderkit(
                self,
                baderkit_object, 
                directory, 
                **kwargs)
            # setattr(self, entry_name, entry)
            
        # save results to db
        data.update(**all_kwargs)
        self.update_from_fields(**data)
        self.save()
