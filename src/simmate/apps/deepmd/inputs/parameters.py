# -*- coding: utf-8 -*-

# For a list of parameter and their defaults look at...
#   https://docs.deepmodeling.org/projects/deepmd/en/master/train/train-input.html

{
    "model": {
        "descriptor": {
            "type": "se_e2_a",
            # "sel": [46, 92],  # Default is Auto
            "neuron": [25, 50, 100],  # Default is [2, 4, 8]
            "axis_neuron": 16,  # Default is 4
        },
        "fitting_net": {
            "neuron": [240, 240, 240],  # Default is [120, 120, 120]
            # "resnet_dt": True,  # Default is False
            # "trainable": True,  # Default is False
            # "atom_ener": [],  # Specify energy in vacuum for each type
        },
    },
    "learning_rate": {},
    "loss": {},
    "training": {
        "training_data": {
            "systems": [
                "../deepmd_data/C7_train",
                "../deepmd_data/C1_train",
                "../deepmd_data/C6_train",
                "../deepmd_data/C4_train",
                "../deepmd_data/C8_train",
                "../deepmd_data/C2_train",
                "../deepmd_data/C5_train",
                "../deepmd_data/C3_train",
                "../deepmd_data/C9_train",
            ]
        },
        "validation_data": {
            "systems": [
                "../deepmd_data/C4_test",
                "../deepmd_data/C8_test",
                "../deepmd_data/C6_test",
                "../deepmd_data/C2_test",
                "../deepmd_data/C5_test",
                "../deepmd_data/C9_test",
                "../deepmd_data/C3_test",
                "../deepmd_data/C7_test",
                "../deepmd_data/C1_test",
            ],
            # "batch_size": 1,  # Default is 1
            "numb_btch": 1,  # Default is 1
        },
        "numb_steps": 1000000,
        # "numb_test": 1,  # Default is 1
    },
}
