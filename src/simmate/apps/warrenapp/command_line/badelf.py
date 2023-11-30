#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 12:27:45 2023

@author: sweav
"""

import logging
from pathlib import Path

import typer
from simmate.toolkit import Structure
from typer import Context
from simmate.command_line.workflows import parse_parameters
from simmate.apps.warrenapp.workflows.badelf.badelf import BadElfAnalysis__Warren__Badelf

"""
This module defines a simple typing CLI function for running BadELF. A similar
and more general function already exists (simmate workflows run-quick), but
is a bit less direct if users just want to use BadELF.
"""



badelf_app = typer.Typer(rich_markup_mode="markdown")

@badelf_app.callback(no_args_is_help=True)
def badelf():
    """A group of commands for running BadELF analysis"""
    pass

@badelf_app.command()
def run(context: Context, 
           directory: Path = typer.Option(Path("."), help="Path to the directory with VASP files"), # we default to the current directory
           find_empties: bool = typer.Option(True, help="Whether or not the algorithm will search for electride sites"),
           min_charge: float = typer.Option(0.45, help="The minimum ELF cutoff for a site to be considered an electride"), # This is somewhat arbitrarily set
           algorithm: str = typer.Option("badelf", help="The algorithm used for partitioning"),
           print_atom_voxels: bool = typer.Option(False, help="Whether or not the algorithm will print the assigned voxels"),
           ):
    """A command for running BadELF analysis"""
    
    # If no directory is specified, assume the user wishes to run in the current
    # directory
    kwargs_cleaned = parse_parameters(context=context)
    structure = Structure.from_file("POSCAR")
    
    result = BadElfAnalysis__Warren__Badelf().run(
        structure=structure,
        directory=directory,
        find_empties=find_empties,
        min_charge=min_charge,
        algorithm=algorithm,
        print_atom_voxels=print_atom_voxels,
        **kwargs_cleaned)
    
    # Let the user know everything succeeded
    if result.is_completed():
        logging.info("Success! All results are also stored in your database.")
