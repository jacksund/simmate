# -*- coding: utf-8 -*-

import pandas as pd
from simmate.apps.badelf.core import Grid
import itertools

class BadelfResults:
    """
    A class for storing results from the BadELF or VoronELF algorithms. 
    """
    def __init__(self, 
                 grid: Grid,
                 array_coords: list = None,
                 charges: list = None,
                 voxel_assignments: pd.DataFrame = None,
                 ):
        self.grid = grid
        if array_coords is None:
            a, b, c = grid.grid_shape
            self.array_coords = [idx for idx in itertools.product(range(a), range(b), range(c))]
        else:
            self.array_coords = array_coords
        
        if charges is None:
            charge_data = grid.total
            self.charges = [float(charge_data[idx[0], idx[1], idx[2]]) for idx in self.array_coords]
        else:
            self.charges = charges
        
        if voxel_assignments is None:
            # Create a dataframe that has each coordinate index and the charge as columns
            # The site column will be filled out throughout partitioning
            all_charge_coords = pd.DataFrame(self.array_coords, columns=["x", "y", "z"]).add(1)

            all_charge_coords["chg"] = self.charges
            all_charge_coords["site"] = None
            self.voxel_assighments = all_charge_coords
        
        
        
                
    
    