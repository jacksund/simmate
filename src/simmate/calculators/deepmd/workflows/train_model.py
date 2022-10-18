# -*- coding: utf-8 -*-

import json
from pathlib import Path

from simmate.toolkit import Composition
from simmate.workflow_engine import S3Workflow


class MlPotential__Deepmd__TrainModel(S3Workflow):

    use_database = False
    monitor = False
    command = "dp train input.json"

    @staticmethod
    def setup(
        directory: Path,
        composition: Composition,
        training_data: list[
            Path
        ],  # consider accepting a Dynamics or IonicStep queryset
        testing_data: list[Path],
        input_filename: str = "input.json",
        model_neuron: list[int] = [10, 20, 40],
        fitting_neuron: list[int] = [120, 120, 120],
        num_training_steps: int = 50,
        **kwargs,
    ):

        # establish list of elements
        elements = [e.symbol for e in composition.elements]

        # make sure training/test directories are strings. They are often
        # given a Path objects
        training_data = [str(p) for p in training_data]
        testing_data = [str(p) for p in testing_data]

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
