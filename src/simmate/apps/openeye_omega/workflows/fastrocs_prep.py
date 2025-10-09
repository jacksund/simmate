# -*- coding: utf-8 -*-

from simmate.apps.openeye_omega.workflows.base import OmegaWorkflow


class ConformerGeneration__OpeneyeOmega__FastrocsPrep(OmegaWorkflow):
    description_doc_short = "runs 2D->3D conversions to be used for FastROCs"

    parameters = dict(
        commentEnergy=True,
        maxConfs=10,
        flipper=True,
        flipper_maxcenters=4,
        progress="percent",
    )
