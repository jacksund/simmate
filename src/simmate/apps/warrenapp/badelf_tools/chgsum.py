#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 11:20:59 2023

@author: sweav
"""

from pymatgen.io.vasp.outputs import Chgcar
from pymatgen.io.vasp.inputs import Poscar
from pathlib import Path

def chgsum(directory: Path):
    aeccar0 = Chgcar.from_file(directory / "AECCAR0")
    aeccar2 = Chgcar.from_file(directory / "AECCAR2")
    poscar = Poscar(aeccar0.structure)
    
    data_total0 = aeccar0.data["total"]
    data_total2 = aeccar2.data["total"]
    
    data_total_sum = data_total0 + data_total2
    data_sum = {"total":data_total_sum}
    
    chgcar_sum = Chgcar(poscar, data_sum)
    chgcar_sum.write_file(directory / "CHGCAR_sum")
