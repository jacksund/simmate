# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..dynamics import Dynamics


class DynamicsComponent(TableComponent):
    table = Dynamics
    display_name = "Dynamics"
