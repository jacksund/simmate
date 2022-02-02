# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DiffusionAnalysis

(
    MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
) = DiffusionAnalysis.create_subclasses("MIT", module=__name__)
