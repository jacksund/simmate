# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 11:26:18 2022

@author: siona
"""
from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow

# training multiple models at the same time
# get starting data (either md run or from table)
# train models for 1 iteration
# run short lammps simulation: 1000 steps?
# compare forces/energy for each 10th or 100th structure from each model
# if models produce different results, run dft calculations with structures and add to dataset
# energy/forces within 5% of each other???
# have running dataset of structures to add??
# make new datasets after each iteration


class MlPotential__Deepmd__BuildFromParallel(Workflow):

    use_database = False

    def run_config(
        structure: Structure,
        directory: Path,
        init_data: str = "md",  # set to either 'md' or 'table'
        table_name: str = "",
        seeds: list = [123, 10, 78],  # length of seeds list = number of models trained
        #!!!what to set numbers as???
        md_kwargs: dict = {"temperature_start": 300, "temperature_end": 300},
    ):

        md_workflow = get_workflow("dynamics.vasp.mit")

        deepmd_workflow = get_workflow("ml-potential.deepmd.train_model")
        freeze_workflow = get_workflow("ml-potential.deepmd.freeze_model")
        lammps_workflow = get_workflow("ml-potential.deepmd.run_lammps")

        # run md to get starting data
        state = md_workflow.run(
            structure=structure,
            **md_kwargs,
        )

        structures = state.result().structures.all()

        # create separate directories for running deepmd and lammps
        deepmd_directory = directory / "deepmd"
        lammps_directory = directory / "lammps"

        # keep running list of training/testing data to add to
        training_data = []
        testing_data = []

        # keep running list of structures from each lammps run (if possible)
        lammps_structures = []

        # keep list of running energies and forces from lamps run
        lammps_energies = []
        lammps_forces = []

        train, test = DeepmdDataset.to_file(
            ionic_step_structures=structures,
            directory=directory / "deepmd_data_init",
        )

        training_data.append(train)
        testing_data.append(test)

        # for each value provided in seeds, run a separate deepmd training
        #!!!run in parallel
        for i, num in enumerate(seeds):
            deepmd_workflow.run(  # ---------------- USE RUN CLOUD IN FINAL VERSION
                directory=deepmd_directory,
                composition=structure.composition,
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input_{i}.json',
                input_filename="input_{i}.json",
                training_data=training_data,
                testing_data=testing_data,
                seed=num,
            )

            # after training is complete, freeze model
            freeze_workflow.run(
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp freeze -o graph_{i}.pb',
            )

            lammps_workflow.run(
                structure=structure,  # pick different starting structure!!!
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; lmp -in in.lmp',  # right command???
                directory=lammps_directory / f"_{i}",
                deepmd_model=f"graph_{i}.pb",
                lammps_timestep=1000,
                lammps_dump_filename=f"dump_{i}.lammpstrj",
            )

            # get structures from lammps run or get the forces/energies
            # add to list

            #!!!check error between structures (use every 10th/100th structure)
            for i, energy_list in enumerate(lammps_energies):
                for n, energy in enumerate(energy_list):
                    # compare energy to energy from same timestep from other simulations
                    difference = abs(energy - lammps_energies[i][n])

            # since force is a list take average difference of entire list
            force_error = True
