# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DynamicsRun

MITDynamicsRun, MITDynamicsIonicStep = DynamicsRun.create_subclasses(
    "MIT",
    module=__name__,
)
