# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..dynamics import Dynamics


class DynamicsTable(DynamicTableForm):
    table = Dynamics
    display_name = "Dynamics"
