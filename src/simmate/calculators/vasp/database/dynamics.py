# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DynamicsRun

MITDynamicsRun, MITDynamicsIonicStep = DynamicsRun.create_subclasses(
    "MIT",
    module=__name__,
)

MatprojDynamicsRun, MatprojDynamicsIonicStep = DynamicsRun.create_subclasses(
    "Matproj",
    module=__name__,
)

(
    MatVirtualLabNPTDynamicsRun,
    MatVirtualLabNPTDynamicsIonicStep,
) = DynamicsRun.create_subclasses(
    "MatVirtualLabNPT",
    module=__name__,
)
