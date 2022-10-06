# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 11:45:07 2022

@author: siona
"""

# input file with starting struct
# relax structure
# MD @ 300, 750 and 1200K
# make deepmd data files
# write deepmd input file
# train model in 3 stages
# start with 300
# restart training after each temp is done
# output = lcurve.out file

from simmate.workflows.utilities import get_workflow
from simmate.workflow_engine import Workflow
from simmate.toolkit import Structure
from simmate.workflow_engine import S3Workflow

from simmate.database import connect
from simmate.database.workflow_results import Dynamics

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset

import json


class Run__Deepmd__Training(S3Workflow):
    use_database = False
    monitor = False
    command = "dp train input.json"

    @staticmethod
    def setup(
        directory,
        structure,
        input_filename,
        training_data,
        testing_data,
        model_neuron=[10, 20, 40],
        fitting_neuron=[120, 120, 120],
        num_training_steps=50,
        **kwargs,
    ):

        # structure = structure.to_toolkit()
        element_list = structure.composition.elements
        type_map = []
        for x in element_list:
            type_map.append(x.symbol)

        dictionary = {
            "model": {
                "type_map": type_map,
                "descriptor": {
                    "type": "se_e2_a",
                    "rcut": 6.0,
                    "neuron": model_neuron,
                },
                "fitting_net": {"type": "ener", "neuron": fitting_neuron},
            },
            "learning_rate": {"type": "exp"},
            "loss": {"type": "ener"},
            "training": {
                "training_data": {"systems": training_data},
                "validation_data": {"systems": testing_data},
                "numb_steps": num_training_steps,
                "disp_file": "lcurve.out",
                "disp_freq": 10,
                "save_freq": 10,
                "save_ckpt": "model.ckpt",
            },
        }

        json_object = json.dumps(dictionary, indent=4)

        with open(input_filename, "w") as outfile:
            outfile.write(json_object)


class Create__Deepmd__Model(Workflow):

    use_database = False

    def run_config(structure, directory, **kwargs):

        # define subdirectory to run relaxation in
        relax_subdirectory = directory / "_relax"

        relax_workflow = get_workflow("relaxation.vasp.quality01")

        # get relaxed structure
        state = relax_workflow.run(
            structure=structure, directory=relax_subdirectory
        )

        relax_result = state.result()

        md_workflow = get_workflow("dynamics.vasp.mit")

        submitted_states = []

        # temps to run md simulations at
        temp_list = [300, 750, 1200]

        for x in temp_list:
            # submit each md run to cloud
            state = md_workflow.run_cloud(
                structure=relax_result,
                temperature_start=x,
                temperature_end=x,
                nsteps=50,
            )

            submitted_states.append(state)

        results = [state.result() for state in submitted_states]

        # iterate through the result of each md simulation and get
        # temperature and list of ionic steps
        # write structure data to files for use with deepmd
        for x in results:
            temp = x.temperature_start
            structures = x.structures.all()
            directory = f"deepmd_data_{temp}"
            DeepmdDataset.to_file(structures)

        composition = results[0].formula_full

        # run initial deepmd training iteration
        Run__Deepmd__Training.run(
            structure=structure,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd3; dp train input_1.json',
            input_filename="input_1.json",
            training_data=[f"deepmd_data_300/{composition}_train"],
            testing_data=[f"deepmd_data_300/{composition}_test"],
        )

        # run additional deepmd training iterations with restart function
        Run__Deepmd__Training.run(
            structure=relax_result.structure,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd3; dp train -restart model.ckpt-50 input_2.json',
            input_filename="input_2.json",
            training_data=[
                f"deepmd_data_300/{composition}_train",
                f"deepmd_data_750/{composition}_train",
            ],
            testing_data=[
                f"deepmd_data_300/{composition}_test",
                f"deepmd_data_750/{composition}_test",
            ],
        )

        Run__Deepmd__Training.run(
            structure=relax_result.structure,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd3; dp train -restart model.ckpt-100 input_3.json',
            input_filename="input_3.json",
            training_data=[
                f"deepmd_data_300/{composition}_train",
                f"deepmd_data_750/{composition}_train",
                f"deepmd_data_1200/{composition}_train",
            ],
            testing_data=[
                f"deepmd_data_300/{composition}_test",
                f"deepmd_data_750/{composition}_test",
                f"deepmd_data_1200/{composition}_test",
            ],
        )
