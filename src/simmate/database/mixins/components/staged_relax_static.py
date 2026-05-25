# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..staged_relax_static import StagedRelaxStatic


class StagedRelaxStaticComponent(TableComponent):
    table = StagedRelaxStatic
    display_name = "Staged Relaxations"
