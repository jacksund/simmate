# -*- coding: utf-8 -*-

import subprocess
import platform
import os
from pathlib import Path
from simmate.toolkit import Structure

class ZeroFluxToolkit:
    """
    A class that interfaces with the [Henkelman group's Bader code](https://theory.cm.utexas.edu/henkelman/code/bader/)
    to allow for easy use during the BadELF algorithm. Note that there are also
    workflows that use this code, but this class does not use the Simmate
    database in any way.
    """
    def __init__(
            self,
            directory: Path = None,
                 ):
        self.directory = directory
    
    def _execute(
            self,
            command: str = "bader CHGCAR -ref ELFCAR",
            ):
        """
        A basic method for running a command.
        
        Args:
            command (str)
        """
        # We add the following line to all of our commands so that the output
        # is printed and we use the weighted method.
        # if "-b weight > bader.out" not in command:
        #     command += " -b weight > bader.out"
        if "> bader.out" not in command:
            command += " > bader.out"
            
        # Begin the process
        process = subprocess.Popen(
            command,
            cwd=self.directory,
            shell=True,
            preexec_fn=None if platform.system() == "Windows"
            # or "mpirun" not in command  # See bug/optimize comment above
            else os.setsid,
            stderr=subprocess.PIPE,
        )
        
        # wait for the process to finish and get any errors.
        # output, errors = process.communicate()
        output, errors = process.communicate()
        # check if the return code is non-zero and thus failed.
        if process.returncode != 0:
            print(process.returncode)
            # convert the error from bytes to a string
            errors = errors.decode("utf-8")
            print(errors)
            # raise Exception(
            #     f"""
            #     The Henkelman bader code was called but failed. This most likely
            #     means that the bader code is not installed or is not in the
            #     PATH.
            #     Alternatively, the command you are trying to run is invalid.
            #     """
            #     )
    
    @staticmethod
    def _get_indices_string(indices: list,):
        """
        Converts a list of indices to a string to be added to a Henkelman
        bader command.
        """
        indices_str = ""
        henkelman_indices = [i+1 for i in indices]
        for index in henkelman_indices:
            indices_str += f" {index}"
        return indices_str
            
    def execute_henkelman_code(
            self,
            charge_file: str,
            partitioning_file: str,
            ):
        """
        Runs the [Henkelman group's Bader code](https://theory.cm.utexas.edu/henkelman/code/bader/)
                  
        Args:
            charge_file (str): The name of the file containing charge density
                data.
                
            partitioning_file (str): The name of the file to use for partitioning.
        """
        self._execute(f"bader {charge_file} -ref {partitioning_file}")
        
    def execute_henkelman_code_sel_atom(
            self,
            charge_file: str,
            partitioning_file: str,
            atoms_to_print: list,
            ):
        """
        Runs the [Henkelman group's Bader code](https://theory.cm.utexas.edu/henkelman/code/bader/)
        with the -sel_atom option to write outputs to a file
        
        Args:
            charge_file (str): 
                The name of the file containing charge density
                data.
            partitioning_file (str): 
                The name of the file to use for partitioning.
            atoms_to_print (list): 
                A list of atom indices to print. Should be
                indices starting at 0.
        """
        indices_str = self._get_indices_string(atoms_to_print)
        self._execute(f"bader {charge_file} -ref {partitioning_file} -p sel_atom {indices_str}")
        
    def execute_henkelman_code_sum_atom(
            self,
            charge_file: str,
            partitioning_file: str,
            species_to_print: list,
            structure: Structure,
            ):
        """

        Parameters
        ----------
        charge_file : str
            The name of the charge file containing charge density data.
        partitioning_file : str
            The name of the file to use for partitioning.
        species_to_print : list
            The symbol of the atom type to print.
        structure : Structure
            The pymatgen structure object for the system of interest.

        Returns
        -------
        None.
        """
        atom_indices = structure.indices_from_symbol(f"{species_to_print}")
        indices_str = self._get_indices_string(atom_indices)
        self._execute(f"bader {charge_file} -ref {partitioning_file} -p sum_atom {indices_str}")
        
        