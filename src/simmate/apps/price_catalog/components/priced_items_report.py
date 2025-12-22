# -*- coding: utf-8 -*-

from simmate.website.htmx.components import HtmxComponent

from ..models import PricedItem, PricePoint


class PricedItemsReport(HtmxComponent):

    template_name = "price_catalog/priced_items/report.html"

    item_names_options: list[str] = None  # set in mount
    years_ago_norm_options: list[int] = PricedItem.years_ago_options

    def mount(self):
        self.item_names_options = list(
            PricedItem.objects.values_list("name", flat=True).all()
        )
        self.form_data = {
            "item_names": ["S&P 500", "Gold", "Chemicals"],
            "use_percent": True,
            "use_inflation_adj": True,
            "years_ago_norm": 10,
        }
        self.process()

    def post_parse(self):
        # BUG: checkbox field does not show in POST data when =False. This is
        # normal HTML behavior to save on bandwidth, but causes a bug here.
        if "use_percent" not in self.post_data.keys():
            self.post_data["use_percent"] = False
        if "use_inflation_adj" not in self.post_data.keys():
            self.post_data["use_inflation_adj"] = False

    def process(self):

        # self.figure = PricedItem.get_report_figure(
        #     names=self.item_names,
        #     years_ago_norm=self.years_ago,
        #     percent=self.use_percent,
        #     inflation_adj=self.use_inflation_adj,
        # )
        self.figure = PricedItem.get_report_figure(
            names=self.form_data["item_names"],
            years_ago_norm=self.form_data["years_ago_norm"],
            percent=self.form_data["use_percent"],
            inflation_adj=self.form_data["use_inflation_adj"],
        )
