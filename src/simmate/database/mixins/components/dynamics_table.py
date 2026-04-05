# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..dynamics import Dynamics


class DynamicsTable(DynamicTableForm):
    table = Dynamics
    display_name = "Dynamics"
