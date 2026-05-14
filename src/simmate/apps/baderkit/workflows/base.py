# -*- coding: utf-8 -*-

import os
from abc import ABC, abstractmethod

from pathlib import Path
from baderkit import Grid

from simmate.database import connect
from simmate.apps.baderkit.models import Baderkit
from simmate.workflows import Workflow


class BaderkitBase(Workflow, ABC):
    """
    This is the base workflow for BaderKit. It should not be run directly.
    """

    use_database = True
    database_table = Baderkit
    
    @classmethod
    @abstractmethod
    def get_baderkit_objects(
        cls,
        directory: Path = None,
        **kwargs
            ):
        raise NotImplementedError()
    
    @classmethod
    def run_config(
        cls,
        source: dict = None,
        directory: Path = None,
        run_id: str = None,
        **kwargs,
    ):
        # get classes
        baderkit_objects = cls.get_baderkit_objects(directory, **kwargs)
        
        # write results to file
        for baderkit_class in baderkit_objects:
            if baderkit_class.spin_system == "not polarized":
                baderkit_class.write_json(directory / f"{baderkit_class.__class__.__name__.lower()}.json")
            else:
                baderkit_class.write_json(directory / f"{baderkit_class.__class__.__name__.lower()}_{baderkit_class.spin_system}.json")
        
        # Get the entry for this run
        database_entry = cls.database_table.objects.get(run_id=run_id)
        database_entry.update_from_baderkit(baderkit_objects=baderkit_objects, directory=directory, **kwargs)
        
        # remove copied files to save space
        for file in cls.use_previous_directory:
            os.remove(directory / file)
            
class BaderkitVaspBase(BaderkitBase):
    """
    This is the base workflow for BaderKit analyses that do not involve Spin. It
    should not be run directly.
    """

    charge_filename = None
    reference_filename = None
    baderkit_class = None
    baderkit_subclasses = []
    
    @classmethod
    def get_baderkit_objects(
        cls,
        directory: Path = None,
        **kwargs
            ):
        # create CHGCAR_sum grid
        grid1 = Grid.from_vasp(directory / "AECCAR0")
        grid2 = Grid.from_vasp(directory / "AECCAR2")
        total_charge_grid = grid1.linear_add(grid2)
        # load CHGCAR
        charge_grid = Grid.from_vasp(directory / cls.charge_filename)
        # load reference
        if cls.reference_filename is not None:
            reference_grid = Grid.from_vasp(directory/cls.reference_filename, total_only=False)
        else:
            reference_grid = total_charge_grid
        # create Bader
        bader = cls.baderkit_class.from_vasp(
            charge_grid=charge_grid,
            reference_grid=reference_grid,
            total_charge_grid=total_charge_grid,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        
        classes = [bader]
        for subclass in cls.baderkit_subclasses:
            test_class = getattr(bader, subclass, None)
            if test_class is None:
                continue
            classes.append(test_class)
        
        return classes
    
class BaderkitVaspSpinBase(BaderkitBase):
    """
    This is the base workflow for BaderKit analyses that do not involve Spin. It
    should not be run directly.
    """

    charge_filename = "CHGCAR"
    reference_filename = None
    baderkit_class = None
    baderkit_subclasses = []
    
    @classmethod
    def get_baderkit_objects(
        cls,
        directory: Path = None,
        **kwargs
            ):
        # create CHGCAR_sum grid
        grid1 = Grid.from_vasp(directory / "AECCAR0")
        grid2 = Grid.from_vasp(directory / "AECCAR2")
        total_charge_grid = grid1.linear_add(grid2)
        
        # load CHGCAR
        charge_grid = Grid.from_vasp(directory/cls.charge_filename, total_only=False)
        
        # load reference
        reference_grid = Grid.from_vasp(directory/cls.reference_filename, total_only=False)
        
        charge_grid_up, charge_grid_down = charge_grid.split_to_spin()
        reference_grid_up, reference_grid_down = reference_grid.split_to_spin()
        
        # Get the badelf toolkit object for running badelf.
        bader_up = cls.baderkit_class.from_vasp(
            charge_grid=charge_grid_up,
            reference_grid=reference_grid_up,
            total_charge_grid=total_charge_grid,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        bader_down = cls.baderkit_class.from_vasp(
            charge_grid=charge_grid_down,
            reference_grid=reference_grid_down,
            total_charge_grid=total_charge_grid,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        
        classes = [bader_up, bader_down]
        for subclass in cls.baderkit_subclasses:
            test_class = getattr(bader_up, subclass, None)
            if test_class is None:
                continue
            classes.append(test_class)
            test_class = getattr(bader_down, subclass, None)
            if test_class is None:
                continue
            classes.append(test_class)
        
        return classes