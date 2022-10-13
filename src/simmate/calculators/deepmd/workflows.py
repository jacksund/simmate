# -*- coding: utf-8 -*-

import json
from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Structure
from simmate.workflow_engine import S3Workflow, Workflow
from simmate.workflows.utilities import get_workflow

# from simmate.database.workflow_results import Dynamics


class Run__Deepmd__Training(S3Workflow):

    use_database = False
    monitor = False
    command = "dp train input.json"

    @staticmethod
    def setup(
        directory: Path,
        structure: Structure,
        training_data: Path,  # consider accepting a Dynamics or IonicStep queryset
        testing_data: Path,
        input_filename: str = "input.json",
        model_neuron: list[int] = [10, 20, 40],
        fitting_neuron: list[int] = [120, 120, 120],
        num_training_steps: int = 50,
        **kwargs,
    ):

        # establish list of elements
        elements = [e.symbol for e in structure.composition.elements]

        # build the full deepmd input settings
        dictionary = {
            "model": {
                "type_map": elements,
                "descriptor": {
                    "type": "se_e2_a",
                    "rcut": 6.0,
                    "neuron": model_neuron,
                    "sel": [180] * len(elements),  # OPTIMIZE
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

        # write input file
        input_file = directory / input_filename
        input_data = json.dumps(dictionary, indent=4)
        with input_file.open("w") as file:
            file.write(input_data)


class Create__Deepmd__Model(Workflow):

    use_database = False

    def run_config(
        structure: Structure,
        directory: Path,
        temperature_list: list[int] = [300, 750, 1200],
        relax_kwargs: dict = {},
        md_kwargs: dict = {},
        **kwargs,
    ):

        # get relaxed structure
        relax_workflow = get_workflow("relaxation.vasp.quality01")
        state = relax_workflow.run(
            structure=structure,
            directory=directory / relax_workflow.name_full,
            **relax_kwargs,
        )
        relax_result = state.result()

        # submit each md run to cloud to run in parallel
        md_workflow = get_workflow("dynamics.vasp.mit")
        submitted_states = []
        for temperature in temperature_list:

            state = md_workflow.run(  # ---------------- USE RUN CLOUD IN FINAL VERSION
                structure=relax_result,
                temperature_start=temperature,
                temperature_end=temperature,  # constant temp for entire run
                **md_kwargs,
            )
            submitted_states.append(state)

        # wait for all dynamics runs to finish
        results = [state.result() for state in submitted_states]

        # iterate through the result of each md simulation and get
        # temperature and list of ionic steps
        # write structure data to files for use with deepmd
        for result in results:
            temp = result.temperature_start
            structures = result.structures.all()
            DeepmdDataset.to_file(
                ionic_step_structures=structures,
                directory=directory / f"deepmd_data_{temp}",
            )

        # training files are named after the composition. To get this, we can
        # simply use the first result (all should be the same)
        composition = results[0].formula_full

        # keep a running list of training and test datasets. We slowly add to
        # this list as we train
        training_data = []
        testing_data = []

        # run initial deepmd training iteration
        temperature = temperature_list[0]
        training_data.append(
            str(directory / f"deepmd_data_{temperature}/{composition}_train")
        )
        testing_data.append(
            str(directory / f"deepmd_data_{temperature}/{composition}_test")
        )

        deepmd_directory = directory / "deepmd"

        Run__Deepmd__Training.run(
            directory=deepmd_directory,
            structure=structure,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input_1.json',
            input_filename="input_1.json",
            training_data=training_data,
            testing_data=testing_data,
            # TODO: consider making a subdirectory for deepmd
        )

        # run additional deepmd training iterations with restart function
        for n, temperature in enumerate(temperature_list[1:]):

            # add the new dataset to our list
            training_data.append(
                str(directory / f"deepmd_data_{temperature}/{composition}_train")
            )
            testing_data.append(
                str(directory / f"deepmd_data_{temperature}/{composition}_test")
            )

            # find the newest available checkpoint file
            number_max = 0  # to keep track of checkpoint number
            checkpoint_file = None
            for file in deepmd_directory.iterdir():
                if "model.ckpt" in file.stem and "-" in file.stem:
                    number = int(file.stem.split("-")[-1])
                    if number > number_max:
                        number_max = number
                        checkpoint_file = file
            # make sure the loop above ended with finding a file
            if not checkpoint_file:
                raise Exception("Unable to detect DeepMD checkpoint file")

            # And continue the model training with this new data
            Run__Deepmd__Training.run(
                directory=deepmd_directory,
                structure=relax_result,
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp train --restart {checkpoint_file.stem} input_{n}.json',
                input_filename=f"input_{n}.json",
                training_data=training_data,
                testing_data=testing_data,
            )


# structure = Structure.from_file("test_structures/NaCl.cif")

# state = Create__Deepmd__Model.run(
#     structure=structure,
#     relax_kwargs=dict(command="mpirun -n 8 vasp_std > vasp.out"),
#     md_kwargs=dict(
#         command="mpirun -n 12 vasp_std > vasp.out",
#         nsteps=50,
#     ),
# )
