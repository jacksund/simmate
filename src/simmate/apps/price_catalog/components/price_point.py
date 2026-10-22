from simmate.website.data_explorer.components import TableComponent

from ..models import PricePoint


class PricePointComponent(TableComponent):
    table = PricePoint
