#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from simmate.apps.deepmd.inputs import DeepmdDataset, DeepmdInput
from simmate.engine import S3Workflow
from simmate.workflows.utilities import get_workflow


class DeepmdTraningWorkflow(S3Workflow):
    _parameter_methods = S3Workflow._parameter_methods  # + others?

    required_files = ["input.json"]

    command: str = "dp --pt train input.json"  # Move to simmate default.
    # --pt indicates pytorch backend, which is what DeepMD used for DPA models

    use_database = False  # The main output of this workflow is a DeepMD model.
    # Eventually this should be tracked and ideally saved to the cloud somehow,
    # but for now I just ignore it.

    # -------------------------------------------------------------------------

    # We set each section of DeepMD-kit's input parameters as a class attribute
    # https://docs.deepmodeling.com/projects/deepmd/en/stable/train/train-input.html

    model: dict = {}
    """
    key-value pairs for the `model` section of `input.json`
    """

    learning_rate: dict = {}
    """
    key-value pairs for the `learning_rate` section of `input.json`
    """

    loss: dict = {}
    """
    key-value pairs for the `loss` section of `input.json`
    """

    training: dict = {}
    """
    key-value pairs for the `training` section of `input.json`
    """

    nvnmd: dict = {}
    """
    key-value pairs for the `nvnmd` section of `input.json`
    """

    @classmethod
    @property
    def full_settings(cls) -> dict:
        return dict(
            model=cls.model,
            learning_rate=cls.learning_rate,
            loss=cls.loss,
            training=cls.training,
            nvnmd=cls.nvnmd,
        )

    # -------------------------------------------------------------------------

    @classmethod
    def get_final_command(
        cls,
        finetune: bool = False,
        pretrained_model: Path | str = "",
        use_model_branch: bool = False,
        model_branch: str = "RANDOM",
        **kwargs,
    ) -> str:
        """
        Builds the command to call DeepMD-kit

        Args:
            finetune (bool): Whether to build a model from scratch or not

            pretrained_model (Path | str): The filepath to the model to be finetuned

            use_model_branch (bool): Whether to use a specific model branch. This
                is necessary for fine-tuning from a multi-task model

            model_branch (str): The name of the branch to finetune. RANDOM will
                instead use a randomly initialized fitting net

            use_pretrain_script (bool): The model section must match the pretrained
                one.

        """
        command_final = cls.command

        # Now go through and add options. We only do this if we want to finetune
        if finetune:
            # add finetuning tag
            command_final += f" --finetune {pretrained_model}"
            # automatically use model section from pretrained model. This must
            # be done to avoid mismatched models
            command_final += " --use-pretrain-script"

            if use_model_branch:
                # add model branch
                command_final += f" --model-branch {model_branch}"

        return command_final

    @classmethod
    def setup(
        cls,
        directory: Path,
        structure_query,
        test_size: float,
        deepmd_system_format: str = "mixed",  # other option is system
        finetune: bool = False,
        **kwargs,
    ):
        # The structure_query can either be a Django query of a table or a dict
        # object with the desired query including the key: 'workflow_name', and
        # optionally any other valid filters
        if isinstance(structure_query, dict):
            # get database object
            workflow = get_workflow(structure_query["workflow_name"])
            data_table = workflow.database_table
            # convert to Django query by filtering database using provided query
            structure_query = data_table.objects.filter(**structure_query)

        # write input structures to deepmd format
        set_config = DeepmdDataset(structure_query)
        if cls.deepmd_system_format == "mixed":
            training_folders, validation_folders, type_map = set_config.to_mixed_type(
                directory, test_size
            )
        elif cls.deepmd_system_format == "system":
            training_folders, validation_folders, type_map = set_config.to_system(
                directory, test_size
            )
        else:
            raise ValueError("deepmd_system_format must be either 'system' or 'mixed'")

        # if we are finetuning, we only need the model section to include type mapping
        # as everything else will automatically fit the pretrained model
        if finetune:
            logging.info(
                "Fine-tuning is selected. This will overwrite any information in the model section except the type_map."
            )
            cls.model = {}

        input_config = DeepmdInput(
            training_folders=training_folders,
            validation_folders=validation_folders,
            type_map=type_map,
            model=cls.model,
            learning_rate=cls.learning_rate,
            loss=cls.loss,
            training=cls.training,
            nvnmd=cls.nvnmd,
        )
        input_config.to_file(directory / "input.json")
