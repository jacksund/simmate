# -*- coding: utf-8 -*-

from pathlib import Path

from deepmd.calculator import DP
from pymatgen.io.ase import AseAtomsAdaptor

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


class MlPotential__Deepmd__Prediction(Workflow):

    use_database = False

    def run_config(
        structure: Structure,  # consider making a list of structures
        directory: Path,  # directory where frozen model (graph.pb file ) is stored
        **kwargs,
    ):

        # set deepmd trained model as calculator
        # assuming name is graph.pb but this depends on what name was used
        # in freeze_model workflow
        # !!! if doesn't work, set type_dict
        calculator = DP(model=directory / "graph.pb")

        # get ase atoms from structure
        structure_atoms = AseAtomsAdaptor.get_atoms(structure)

        # set calculator for ase object to deepmd calculator
        structure_atoms.calc = calculator

        # calculate values
        deepmd_energy = structure_atoms.get_potential_energy()
        deepmd_forces = structure_atoms.get_forces()

        # can deepmd model be used to predict other parameters??

        return {"energy": deepmd_energy, "forces": deepmd_forces}
