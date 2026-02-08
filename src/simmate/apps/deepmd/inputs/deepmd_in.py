#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path


class DeepmdInput:
    """
    Basic input class for DeepMD.

    This class is a wrap around for DeepMD's input parameters:
        https://docs.deepmodeling.com/projects/deepmd/en/stable/train/train-input.html
    """

    def __init__(
        self,
        training_folders: list = [],
        validation_folders: list = [],
        type_map: list = [],
        model: dict = {},
        learning_rate: dict = {},
        loss: dict = {},
        training: dict = {},
        nvnmd: dict = {},
    ):
        """
        Initializes a input.json file.
        """
        self.training_folders = (training_folders,)
        self.validation_folders = (validation_folders,)
        self.type_map = (type_map,)
        self.model = model
        self.learning_rate = learning_rate
        self.loss = loss
        self.training = training
        self.nvnmd = nvnmd

    # -------------------------------------------------------------------------

    # Loading methods

    @classmethod
    def from_file(cls, filename: Path | str = "input.json"):
        """
        Builds a DeepmdInput object from a file.
        """
        filename = Path(filename)
        with filename.open() as file:
            content = json.load(file)
        return cls.from_dict(content)

    @classmethod
    def from_dict(cls, content: dict):
        try:
            # Attempt to load input data from dictionary
            return cls(
                # These three settings must be present, so we don't use .get()
                training_folders=content["training"]["training_data"]["systems"],
                validation_folders=content["training"]["validation_data"]["systems"],
                type_map=content["model"]["type_map"],
                # The settings in these sections can be optional, so we use .get()
                model=content.get("model", {}),
                learning_rate=content.get("learning_rate", {}),
                loss=content.get("loss", {}),
                training=content.get("training", {}),
                nvnmd=content.get("nvnmd", {}),
            )
        except:
            raise Exception(
                "Input data must include training_data, validation_data, and type_map"
            )

    # -------------------------------------------------------------------------

    # Writing methods
    @classmethod
    def to_file(cls, filename: Path | str = "input.json"):
        """
        Writes DeepmdInput to .json file
        """
        filename = Path(filename)
        with filename.open() as file:
            json.dump(cls.to_dict(), file)

    @classmethod
    def to_dict(cls):
        cls.training["training_data"]["systems"] = cls.training_folders
        cls.training["validation_data"]["systems"] = cls.validation_folders
        cls.model["type_map"] = cls.type_map
        return {
            "model": cls.model,
            "learning_rate": cls.learning_rate,
            "loss": cls.loss,
            "training": cls.training,
            "nvnmd": cls.nvnmd,
        }
