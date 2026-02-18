# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 11:47:53 2025

@author: Sam
"""

from simmate.apps.deepmd.workflows.base import DeepmdTraningWorkflow


class DeepmdModel__Deepmd__Dpa2Medium(DeepmdTraningWorkflow):
    """
    This is a DeepMD's DPA-2 model set up with a medium size. This workflow is
    designed to train a model from scratch and does not incorporate DPA-2's
    multi-task abilities
    We use the exact example setup here:
    https://github.com/deepmodeling/deepmd-kit/blob/devel/examples/water/dpa2/input_torch_medium.json
    """

    model = {
        # Note we don't include a "type_map" as this will be automatically filled out
        # in the workflow
        "descriptor": {  # Settings related to descripter net of model
            "type": "dpa2",
            "repinit": {
                "tebd_dim": 8,  # dimension of atom type embedding
                "rcut": 6.0,  # cut-off radius around atoms
                "rcut_smth": 0.5,  # cutoff is made to smoothly go to 0. This is where that starts
                "nsel": 120,  # max number of selected neighbors
                "neuron": [
                    25,
                    50,
                    100,
                ],  # number of neurons in each hidden layer (this is default)
                "axis_neuron": 12,  # size of embedding matrix
                "activation_function": "tanh",  # activation function in embedding net
                "three_body_sel": 48,  # max number of neighbors in 3-body rep
                "three_body_rcut": 4.0,  # cutoff radius in 3-body rep
                "three_body_rcut_smth": 3.5,  # where radius starts to smooth (default is 0.5)
                "use_three_body": True,
            },  # End repinit
            "repformer": {
                "rcut": 4.0,
                "rcut_smth": 3.5,
                "nsel": 48,
                "nlayers": 6,  # number of repformer layers
                "g1_dim": 128,  # dimension of invariant single-atom rep
                "g2_dim": 32,  # dimension of invariant two-atom rep
                "attn2_hidden": 32,  # hidden dimension of gated self-attention to update g2 rep
                "attn2_nhead": 4,  # number of heads in gated self-attention to update g2 rep
                "attn1_hidden": 128,  # hidden dimension of localized self-attention to update the g1 rep.
                "attn1_nhead": 4,  # number of heads in localized self-attention to update the g1 rep.
                "axis_neuron": 4,  # number of dimension of submatrix in symm ops
                "update_h2": False,
                "update_g1_has_conv": True,  # update g1 rep with convolution term
                "update_g1_has_grrg": True,  # update g1 rep with grrg term
                "update_g1_has_drrd": True,  # update g1 rep with drrd term
                "update_g1_has_attn": False,  # etc.
                "update_g2_has_g1g1": False,
                "update_g2_has_attn": True,
                "update_style": "res_residual",  # method of updating representations
                "update_residual": 0.01,  # initial std of residual vector weights
                "update_residual_init": "norm",  # initialization method of residual vector weights
                "attn2_has_gate": True,
                "use_sqrt_nnei": True,  # use sqrt of number of neighbors for symm op normalization
                "g1_out_conv": True,  # put the convolutional update of g1 separately outside the concatenated MLP update
                "g1_out_mlp": True,  # put the self MLP update of g1 separately outside the concatenated MLP update
            },  # End reformer
            "precision": "float64",  # degree of precision in embedding net
            "add_tebd_to_repinit_out": False,  # don't add type embedding before input into repformer
        },  # End descriptor
        "fitting_net": {  # Settings related to property fitting net of model
            # Defaults to fitting to energy
            "neuron": [240, 240, 240],  # number of neurons in each hidden layer
            "resnet_dt": True,  # use Timestep in skip connection
            "precision": "float64",  # precision in fitting net
            "seed": 1,  # random seed for parameter initialization
            "_comment": " that's all",
        },  # End fitting net
        "_comment": " that's all",
    }  # End model

    learning_rate = {
        "type": "exp",  # default and only type
        "decay_steps": 5000,  # Learning rate decays after this many training steps
        "start_lr": 0.001,  # initial learning rate
        "stop_lr": 3.51e-08,  # minimum learning rate/learning rate at end of training
        "_comment": "that's all",
    }

    loss = {
        "type": "ener",  # set based on fitting net
        "start_pref_e": 0.02,  # prefactor of energy loss at start of training
        "limit_pref_e": 1,  # prefactor of energy loss at end of training
        "start_pref_f": 1000,  # same as above but for force
        "limit_pref_f": 1,
        "start_pref_v": 0,  # ignore virial
        "limit_pref_v": 0,
        "_comment": " that's all",
    }

    training = {
        "stat_file": "./dpa2.hdf5",  # filepath for saving data statistics. Avoid recalculations
        "training_data": {
            # We don't include systems as these are automatically added by the workflow
            "batch_size": 1,  # indicates all systems use same batch size
            "_comment": "that's all",
        },
        "validation_data": {
            # Systems are automatically added by the workflow
            "batch_size": 1,
            "_comment": "that's all",
        },
        "numb_steps": 1000000,  # number of training batch. Each training uses one batch of data
        "warmup_steps": 0,  # number of steps for learning rate warmup. Start at 0 and increase to start_lr
        "gradient_max_norm": 5.0,  # clips gradient norm to max value
        "seed": 10,  # random seed for getting frames of data
        "disp_file": "lcurve.out",  # file for printing learning curve
        "disp_freq": 100,  # frequency of printing learning curve
        "save_freq": 2000,  # frequency of saving checkpoint
        "_comment": "that's all",
    }
